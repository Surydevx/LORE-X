---
icon: lucide/layers
---

# Architecture

This document describes the internal architecture of LORE-X: the 4-stage pipeline, the mathematical retrieval model, the database schema, and the self-correcting feedback loop.

---

## System Pipeline

LORE-X operates a 4-stage pipeline from raw Git data to queryable architectural memory:

```
Git Repository
     │
     ▼
┌─────────────────────────┐
│ 1. Ingestion Adapter    │  async Git log parsing, heuristic filtering,
│    (local_git.py)       │  idempotent commit deduplication
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 2. Extraction Engine    │  LLM-powered tuple extraction via LiteLLM,
│    (extraction.py)      │  Jinja2 prompt templates, graceful fallback
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 3. Retrieval Engine     │  4-dimensional hybrid scoring:
│    (retrieval.py)       │  semantic + graph + temporal + outcome
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 4. Revision Engine      │  APM webhook-driven outcome recording,
│    (revision.py)        │  automatic status degradation & DAG linking
└─────────────────────────┘
```

---

## Stage 1: Ingestion

**File:** `lorex/vcs/local_git.py`

The `GitLogIngester` class asynchronously parses Git history using `asyncio.create_subprocess_exec` (no shell injection risk). Key behaviors:

- **Custom separator**: Uses `---LOREX_COMMIT_SEP---` in `git log --format` to reliably split multi-line commits.
- **Metadata extraction**: Parses `AuthorName`, `AuthorEmail`, and `Date` (ISO 8601) from each commit block.
- **Heuristic filtering**: Drops trivial commits where the message is under 30 characters, or contains noise keywords (`lint`, `typo`, `bump`, `format`, `merge`) using word-boundary matching.
- **Idempotent deduplication**: Before processing, queries the `Experience` table for all existing `commit_hash` values. Already-ingested commits are silently skipped.
- **Concurrency throttling**: LLM extraction is parallelized via `asyncio.gather` but rate-limited by an `asyncio.Semaphore(5)` to prevent API 429 errors.
- **Thread-safe sessions**: Each extraction thread spawns its own `SessionLocal()` to avoid cross-thread SQLAlchemy contamination.

---

## Stage 2: Extraction

**Files:** `lorex/engine/extraction.py`, `lorex/engine/llm.py`

### LLM Client

The `LLMClient` class routes to one of three LLM providers based on environment variable priority:

1. `GEMINI_API_KEY` → `gemini/gemini-3.6-flash` (with `response_format: json_object`)
2. `OPENAI_API_KEY` → `gpt-4o-mini` (with `response_format: json_object`)
3. `ANTHROPIC_API_KEY` → `claude-3-haiku-20240307` (no `response_format` — Anthropic doesn't support it)

All calls go through [LiteLLM](https://github.com/BerriAI/litellm) for a unified interface. Token usage and latency are traced to stderr.

The response is sanitized by stripping markdown code fences (`` ```json `` / `` ``` ``), parsing the JSON, and safely coercing the `status` field into a `StatusEnum`. Invalid status values default to `VERIFIED`.

### Experience Extractor

The `ExperienceExtractor` renders a Jinja2 prompt template (`lorex/prompts/extraction.jinja2`) and passes it to the LLM. If the LLM call fails, the extractor falls back to a **degraded extraction** that parses the commit message heuristically:

- Sets `status = PARTIALLY_VERIFIED` and `confidence = 0.1`
- Extracts the first meaningful line as the `action`
- Truncates the raw commit body to 500 characters to prevent database bloat

### PyInstaller Support

Both `extraction.py` and `app.py` use a `get_asset_path()` helper that resolves paths via `sys._MEIPASS` when running inside a PyInstaller `--onefile` bundle.

---

## Stage 3: Hybrid Retrieval

**File:** `lorex/engine/retrieval.py`

The `HybridRetrievalEngine` scores every experience against a query using four weighted dimensions:

$$
S_{total} = \alpha \cdot S_{semantic} + \beta \cdot S_{graph} + \gamma \cdot S_{temporal} + \delta \cdot S_{outcome}
$$

### Default Weights (Bayesian-Optimized)

| Weight | Value | Dimension |
|--------|-------|-----------|
| $\alpha$ | 0.352 | Semantic relevance |
| $\beta$ | 0.649 | Graph topology (DAG lineage) |
| $\gamma$ | 0.660 | Temporal validity |
| $\delta$ | 0.736 | Outcome status |

### Scoring Functions

**Semantic ($S_{semantic}$):** Falls back to **Jaccard lexical token overlap** between the query and the experience's `problem + action + conditions` fields. Full embedding-based cosine similarity is architected but not yet wired in.

**Graph ($S_{graph}$):** Scores based on DAG position:
- `0.2` if the node has been superseded (has `superseded_by` set)
- `0.8` if the node supersedes others (is the modern descendant)
- `0.5` for standalone nodes

**Temporal ($S_{temporal}$):** 
- `1.0` for active decisions
- `0.5` for `FAILED` decisions
- `0.2` for decisions past their `valid_until` date
- `0.1` for `SUPERSEDED` decisions

**Outcome ($S_{outcome}$):**
- `VERIFIED` → 1.0
- `PARTIALLY_VERIFIED` → 0.7
- `CONDITIONALLY_VALID` → 0.6
- `FAILED` → 0.1
- `SUPERSEDED` → 0.05

### Bayesian Optimization

The weights are tunable via the Optuna-powered optimization script at `scripts/optimize.py`. This runs a trial loop that drops and recreates the in-memory SQLite schema per trial to guarantee isolation.

---

## Stage 4: Revision Engine

**File:** `lorex/engine/revision.py`

The `RevisionEngine` implements the self-correcting feedback loop. When `record_outcome()` is called (either via the API or the APM webhook):

1. **Exact match** (outcome + conditions match) → Status upgraded to `VERIFIED`.
2. **Outcome match, conditions differ** → Old experience marked `SUPERSEDED`, new experience created with status `CONDITIONALLY_VALID`.
3. **Outcome mismatch** → Old experience marked `SUPERSEDED`, new experience created with status `FAILED`.

In cases 2 and 3, the old experience gets `valid_until = now`, `superseded_by = new_experience.id`, forming a directed edge in the knowledge DAG.

---

## Database Schema

**Files:** `lorex/db/schema.py`, `lorex/db/session.py`

LORE-X uses SQLAlchemy ORM with SQLite (WAL mode enabled for concurrent read/write). The schema consists of five tables:

| Table | Purpose |
|-------|---------|
| `projects` | Project namespace isolation |
| `engineering_events` | Raw ingested events (commits) with full metadata |
| `experiences` | Extracted Experience Tuples with lifecycle fields |
| `evidences` | Evidence records linked to experiences |
| `embeddings` | Vector embeddings linked to experiences (JSON-stored) |

### Key Relationships

- `Project` → has many `EngineeringEvent` and `Experience` (cascade delete)
- `Experience` → has many `Evidence` and `Embedding` (cascade delete)
- `Experience` → self-referential `superseded_by` foreign key (DAG edges)

### Session Management

- `get_db()`: FastAPI dependency generator with `try/except/finally` for proper rollback and cleanup.
- `get_session()`: Raw session factory for CLI scripts and tests.
- SQLite is configured with `check_same_thread=False`, `timeout=30`, and `pool_pre_ping=True`.
- `expire_on_commit=False` is set to support `asyncio.to_thread` usage during ingestion.

---

## Frontend

**File:** `lorex/api/static/index.html`

The dashboard is a single-page application built with:

- **Tailwind CSS** (via CDN) — glassmorphism `bg-white/5 backdrop-blur-xl` aesthetic on true-black background
- **Mermaid.js** — Interactive lineage graphs with click-to-inspect node details
- **Canvas 2D** — 3D dot-wave particle physics engine with mouse-repulsion interaction

All dynamic content is sanitized through an `escapeHTML()` function before any `innerHTML` assignment to prevent XSS. The timeline view uses a non-mutating `[...data.nodes].sort()` to preserve the original graph data.
