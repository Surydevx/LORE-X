---
icon: lucide/rocket
---

# LORE-X Documentation

Welcome to the LORE-X technical documentation. These docs cover the system architecture, API surface, CLI usage, and internal engine design.

## Table of Contents

- [Architecture](architecture.md) — System design, retrieval mathematics, and ingestion pipeline
- [CLI Guide](cli.md) — Full reference for all `lorex` commands
- [API Reference](api.md) — REST endpoint specifications, request/response schemas, and webhook integration
- [Configuration](configuration.md) — Environment variables, `.env` handling, and provider setup
- [Development](development.md) — Contributing, testing, optimization, and project structure

---

## What is LORE-X?

LORE-X is an autonomous architectural memory engine for engineering teams. It passively monitors Git activity, extracts the intent behind architectural decisions using LLMs, and stores them as structured Experience Tuples with full lifecycle tracking.

Unlike conventional RAG systems that retrieve documents based solely on semantic text overlap, LORE-X understands that decisions age, fail, and get superseded. Its Hybrid Retrieval Engine factors in temporal validity, outcome status, and graph lineage alongside semantic relevance — eliminating temporal hallucination entirely.

### The Experience Tuple

Every architectural decision is captured as a 7-dimensional tuple $(P, A, C, V, O, T, S)$:

| Dimension | Description |
|-----------|-------------|
| **Problem** ($P$) | The engineering challenge that triggered the decision |
| **Action** ($A$) | The specific architectural decision applied |
| **Conditions** ($C$) | Boundary conditions under which the action is valid |
| **Evidence** ($V$) | Concrete artifacts backing the decision (commit SHAs, PR links) |
| **Outcome** ($O$) | The empirical result observed after applying the action |
| **Temporal Validity** ($T$) | The lifespan of the decision (from `valid_from` until `valid_until`) |
| **Status** ($S$) | Current health: `VERIFIED`, `PARTIALLY_VERIFIED`, `CONDITIONALLY_VALID`, `SUPERSEDED`, or `FAILED` |

### Quick Start

```bash
# Install globally via uv
uv tool install git+https://github.com/Surydevx/LORE-X.git

# Initialize in your repo
cd /path/to/your/repo
lorex init

# Ingest commit history
lorex ingest . --limit 20

# Explore
lorex log
lorex query "database connection pooling"
lorex serve
```
