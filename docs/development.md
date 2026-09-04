---
icon: lucide/git-branch
---

# Development

Guide for contributing to LORE-X, running tests, and understanding the project layout.

---

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- [`git`](https://git-scm.com/)

---

## Setup

```bash
git clone https://github.com/Surydevx/LORE-X.git
cd LORE-X
uv sync
```

This installs all runtime and dev dependencies defined in `pyproject.toml`.

---

## Project Structure

```
LORE-X/
├── lorex/                     # Main package
│   ├── cli.py                 # CLI entry point (init, ingest, query, log, graph, serve)
│   ├── api/
│   │   ├── app.py             # FastAPI app, lifespan, middleware, exception handlers
│   │   ├── routes/
│   │   │   ├── events.py      # POST /api/events, POST /api/events/vcs/ingest-local
│   │   │   ├── query.py       # POST /api/query
│   │   │   ├── outcomes.py    # POST /api/outcomes, POST /api/outcomes/apm-webhook
│   │   │   └── graph.py       # GET /api/graph
│   │   └── static/
│   │       └── index.html     # Dashboard (Tailwind + Mermaid.js + Canvas particle engine)
│   ├── core/
│   │   ├── models.py          # Pydantic models: ExperienceTuple, StatusEnum
│   │   ├── graph.py           # Cycle detection (DFS-based)
│   │   └── metrics.py         # Carbon impact calculator
│   ├── db/
│   │   ├── schema.py          # SQLAlchemy ORM: Project, EngineeringEvent, Experience, Evidence, Embedding
│   │   └── session.py         # Engine, SessionLocal, init_db, get_db, WAL mode
│   ├── engine/
│   │   ├── extraction.py      # ExperienceExtractor: LLM extraction + degraded fallback
│   │   ├── llm.py             # LLMClient: LiteLLM routing, .env parsing, JSON sanitization
│   │   ├── retrieval.py       # HybridRetrievalEngine: 4-dimensional scoring
│   │   └── revision.py        # RevisionEngine: outcome recording, DAG linking
│   ├── prompts/
│   │   └── extraction.jinja2  # Jinja2 prompt template for LLM extraction
│   └── vcs/
│       └── local_git.py       # GitLogIngester: async git log, heuristic filter, idempotent dedup
├── tests/
│   ├── conftest.py            # Sets DATABASE_URL=sqlite:///:memory: for test isolation
│   ├── test_api.py            # FastAPI TestClient integration tests (5 tests)
│   ├── test_lorex_core.py     # Unit tests: serialization, cycle detection, metrics, revision (4 tests)
│   └── test_retrieval_and_extraction.py  # Extraction fallback + retrieval ranking tests (2 tests)
├── scripts/
│   ├── run_demo.py            # 5-phase demo scenario
│   ├── evaluate.py            # Benchmark: LORE-X vs baseline LLM vs standard RAG
│   └── optimize.py            # Bayesian weight optimization via Optuna
├── docs/                      # Documentation (you are here)
├── pyproject.toml             # Build config, dependencies, entry points
└── pytest.ini                 # Test configuration
```

---

## Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework for the API and dashboard |
| `uvicorn` | ASGI server |
| `pydantic` | Data validation and serialization |
| `sqlalchemy` | Database ORM |
| `jinja2` | Prompt templating for LLM extraction |
| `litellm` | Unified LLM API client (Gemini, OpenAI, Anthropic) |
| `python-dotenv` | `.env` file loading |
| `rich` | Terminal tables and tree rendering for `lorex log` and `lorex graph` |
| `httpx` | HTTP client (used by FastAPI TestClient) |
| `aiofiles` | Async file operations |

### Dev

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `optuna` | Bayesian hyperparameter optimization |

---

## Running Tests

```bash
uv run pytest -v
```

Tests use an in-memory SQLite database (`sqlite:///:memory:`) set in `tests/conftest.py`. This ensures complete isolation — no `lorex.db` file is created or modified during testing.

The test suite consists of 11 tests:

| File | Tests | Coverage |
|------|-------|----------|
| `test_api.py` | 5 | Health check, event ingestion, query, outcome recording, graph retrieval |
| `test_lorex_core.py` | 4 | ExperienceTuple serialization, cycle detection, carbon metrics, revision engine |
| `test_retrieval_and_extraction.py` | 2 | Extraction fallback, hybrid retrieval ranking (VERIFIED > FAILED > SUPERSEDED) |

### Test Architecture

- **`test_api.py`** uses FastAPI's `TestClient` with a dependency override (`get_db` → in-memory session) and an `autouse` fixture that creates/drops tables between tests.
- **`test_lorex_core.py`** and **`test_retrieval_and_extraction.py`** use `get_session()` with `try/finally` guarded cleanup.

---

## Scripts

### `scripts/run_demo.py`

Runs a 5-phase demonstration:
1. Schema initialization
2. Event ingestion
3. Experience extraction
4. Hybrid retrieval query
5. Outcome revision with self-correcting graph

### `scripts/evaluate.py`

Benchmarks LORE-X against baseline LLM and standard RAG on 10 deterministic lifecycle questions. Measures recommendation accuracy, temporal accuracy, and evidence grounding rate.

### `scripts/optimize.py`

Uses Optuna to Bayesian-optimize the retrieval weights ($\alpha, \beta, \gamma, \delta$). Each trial drops and recreates the in-memory SQLite schema for isolation.

```bash
uv run python scripts/optimize.py
```

---

## PyInstaller Bundling

LORE-X supports packaging as a `--onefile` binary. Key considerations:

- Static assets and Jinja2 templates are resolved via `sys._MEIPASS` using `get_asset_path()` helpers in `app.py` and `extraction.py`.
- `uvicorn.run()` uses `reload=False` to prevent subprocess crashes inside the frozen binary.
- The manual `.env` parser in `llm.py` serves as a fallback when `python-dotenv` is unavailable in the bundled environment.

Add data files to your `.spec` file:

```python
datas=[
    ('lorex/api/static', 'lorex/api/static'),
    ('lorex/prompts', 'lorex/prompts'),
]
```
