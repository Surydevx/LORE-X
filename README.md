# LORE-X: Living Organizational Record Engine

<p align="center">
  <strong>Autonomous, self-correcting architectural memory for engineering teams.</strong>
</p>

LORE-X passively monitors your engineering workflow via Git hooks, extracts the intent behind every architectural decision using LLMs, and maps them into a structured 7-dimensional tuple: **$(P, A, C, V, O, T, S)$**. When integrated with your observability stack, LORE-X continuously validates these historical decisions against live production telemetry — automatically degrading the confidence of patterns that fail at scale.

---

## The Problem

Conventional search and RAG architectures retrieve documents based purely on semantic text overlap. They cannot distinguish between an architectural decision that was highly effective in 2021 and one that became a catastrophic anti-pattern at production scale today.

LORE-X solves this by preserving institutional knowledge as a strict mathematical tuple with full lifecycle tracking.

---

## The Mathematical Model

Every architectural decision is modeled as a 7-dimensional tuple:

| Symbol | Dimension | Description | Example |
|--------|-----------|-------------|---------|
| **$P$** | Problem | The engineering challenge | *API latency spikes under load* |
| **$A$** | Action | The architectural decision | *Implemented Redis connection pooling* |
| **$C$** | Conditions | Operational boundaries | *< 10k concurrent users* |
| **$V$** | Evidence | Empirical backing | *Commit SHAs, PR links, APM logs* |
| **$O$** | Outcome | Observed result | *Latency reduced by 35%* |
| **$T$** | Temporal Validity | Decision lifespan | *2024-01-15 → superseded 2024-09-01* |
| **$S$** | Status | Current health | `VERIFIED` · `PARTIALLY_VERIFIED` · `CONDITIONALLY_VALID` · `SUPERSEDED` · `FAILED` |

---

## Core Features

- **Zero-Touch Git Integration** — Automatically intercepts `git commit` events via a `post-commit` hook. No workflow changes required.
- **LLM Extraction Engine** — Synthesizes raw commit data into structured Experience Tuples using Gemini, OpenAI, or Anthropic. Graceful fallback to commit-message parsing when no API key is available.
- **Hybrid Retrieval Engine** — Ranks past decisions using a weighted combination of Semantic Relevance, Graph Lineage, Temporal Validity, and Outcome Status.
- **Self-Correcting Memory Graph** — APM webhook endpoint allows your telemetry stack (Datadog, PagerDuty, Prometheus) to autonomously downgrade failing architectural patterns.
- **Idempotent Ingestion** — Exact-once processing of commit hashes prevents database bloat on repeated syncs.
- **Rich Terminal Output** — `lorex log` and `lorex graph` render styled tables and knowledge trees directly in the terminal using [Rich](https://github.com/Textualize/rich).
- **Interactive Dashboard** — Dark-mode glassmorphism UI with 3D particle physics, Mermaid.js lineage graphs, and a timeline view.

---

## Installation

### Quick Install (Recommended)

Pre-requisites: [`uv`](https://docs.astral.sh/uv/#installation) and [`git`](https://git-scm.com/install/).

```bash
uv tool install git+https://github.com/Surydevx/LORE-X.git
```

This installs the `lorex` CLI globally — no clone needed.

### From Source

```bash
git clone https://github.com/Surydevx/LORE-X.git
cd LORE-X
uv sync
```

### As a Standalone Binary

LORE-X can also be distributed as a PyInstaller `--onefile` binary with no runtime dependencies:

```bash
chmod +x lorex
sudo mv lorex /usr/local/bin/
```

---

## Quickstart

```bash
# 1. Navigate to your Git repository
cd /path/to/your/repo

# 2. Initialize LORE-X (sets up database, .env, .gitignore, post-commit hook)
lorex init

# 3. Backfill existing history
lorex ingest . --limit 20

# 4. View extraction history in the terminal
lorex log

# 5. View the knowledge graph as a tree
lorex graph

# 6. Query past decisions
lorex query "API latency under load"

# 7. Launch the web dashboard
lorex serve
```

Open your browser to `http://localhost:8000/dashboard`.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `lorex init` | Bootstraps `.env`, database schema, `.gitignore` entries, and `post-commit` hook. Prompts for an API key if none is detected. |
| `lorex ingest <path>` | Scans a Git repository and extracts architectural decisions. Supports `--limit` and `--project`. |
| `lorex query "<text>"` | Runs a hybrid retrieval query against the memory graph from the terminal. |
| `lorex log` | Displays recent extractions as a styled terminal table. Supports `--limit` and `--project`. |
| `lorex graph` | Renders the knowledge graph as an interactive terminal tree. Supports `--limit` and `--project`. |
| `lorex serve` | Starts the Uvicorn ASGI server and hosts the interactive dashboard. Supports `--port`. |

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events` | `POST` | Ingest a single engineering event and extract an experience |
| `/api/events/vcs/ingest-local` | `POST` | Batch-ingest commits from a local Git repository |
| `/api/query` | `POST` | Run a hybrid retrieval query. Returns ranked experiences with scores |
| `/api/outcomes` | `POST` | Record an observed outcome against an existing experience |
| `/api/outcomes/apm-webhook` | `POST` | APM telemetry webhook for autonomous graph degradation |
| `/api/graph` | `GET` | Retrieve the full experience lineage graph (nodes + edges) |
| `/health` | `GET` | Health check endpoint |
| `/dashboard` | `GET` | Redirects to the interactive web dashboard |

---

## APM Webhook Integration

Point your APM alerting system to the webhook endpoint to enable the self-correcting graph:

**Endpoint:** `POST /api/outcomes/apm-webhook`

**Payload:**
```json
{
  "incident_id": "inc-9923",
  "breached_metric": "p99_latency_ms",
  "target_node_id": "<experience-id>",
  "auth_token": "<LOREX_WEBHOOK_SECRET>"
}
```

Set the `LOREX_WEBHOOK_SECRET` environment variable to enable authentication. When an alert fires, LORE-X semantically matches the failure against active decisions and downgrades matching `VERIFIED` nodes to `FAILED` or `CONDITIONALLY_VALID`.

---

## Configuration

LORE-X reads configuration from environment variables or a `.env` file in the working directory. The `.env` file is automatically loaded at CLI startup via `python-dotenv`, and during ingestion the target repository's `.env` takes precedence.

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | One of three | Google AI Studio API key (default provider) |
| `OPENAI_API_KEY` | One of three | OpenAI API key |
| `ANTHROPIC_API_KEY` | One of three | Anthropic API key |
| `DATABASE_URL` | No | SQLAlchemy database URL. Defaults to `sqlite:///lorex.db` |
| `LOREX_WEBHOOK_SECRET` | No | Shared secret for APM webhook authentication |

**Provider priority:** Gemini → OpenAI → Anthropic. The first available key wins.

---

## Project Structure

```
lorex/
├── api/
│   ├── app.py              # FastAPI application, middleware, exception handlers
│   ├── routes/
│   │   ├── events.py       # Event ingestion endpoints
│   │   ├── query.py        # Hybrid retrieval query endpoint
│   │   ├── outcomes.py     # Outcome recording & APM webhook
│   │   └── graph.py        # Experience lineage graph endpoint
│   └── static/
│       └── index.html      # Dashboard UI (Tailwind + Mermaid.js)
├── core/
│   ├── models.py           # Pydantic models (ExperienceTuple, StatusEnum)
│   ├── graph.py            # Cycle detection for dependency graphs
│   └── metrics.py          # Carbon impact calculator
├── db/
│   ├── schema.py           # SQLAlchemy ORM models
│   └── session.py          # Database engine, session factory, WAL mode
├── engine/
│   ├── extraction.py       # LLM-powered experience extraction with fallback
│   ├── llm.py              # LiteLLM client, model routing, .env parser
│   ├── retrieval.py        # Hybrid retrieval engine (4-dimensional scoring)
│   └── revision.py         # Outcome recording & experience revision
├── prompts/
│   └── extraction.jinja2   # Jinja2 prompt template for LLM extraction
├── vcs/
│   └── local_git.py        # Async Git log ingestion with semaphore throttling
└── cli.py                  # CLI entry point (init, ingest, query, log, graph, serve)
```

---

## Development

```bash
# Install with dev dependencies
uv sync

# Run the test suite
uv run pytest -v

# Run the evaluation benchmark
uv run python scripts/evaluate.py

# Run Bayesian weight optimization
uv run python scripts/optimize.py

# Run the 5-phase demo scenario
uv run python scripts/run_demo.py
```

---

## Security

- **Local-first storage** — All data stays in `lorex.db` on your machine. Nothing is sent upstream.
- **XSS protection** — All user-supplied and LLM-generated data is sanitized via `escapeHTML()` before DOM injection.
- **Shell injection prevention** — Subprocess calls use `asyncio.create_subprocess_exec` with argument arrays, not shell strings.
- **Webhook authentication** — APM webhook endpoint supports shared-secret token verification.
- **Session safety** — All database sessions use `try/finally` cleanup. Async ingestion spawns per-thread sessions to prevent cross-thread SQLAlchemy contamination.

---

## License

This project is released under the [MIT License](LICENSE).
