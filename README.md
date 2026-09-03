# LORE-X: The Self-Healing Architectural Memory Engine

LORE-X completely automates the documentation of architectural decisions. By passively monitoring your engineering workflow via Git hooks, it tracks your team's decisions and maps them into a robust mathematical tuple: $(P, A, C, V, O, T, S)$.

## Core Features

- **Zero-Touch Git Integration:** Automatically intercepts and ingests `git commit` logs in the background without altering developer workflow.
- **LLM Heuristic Extraction:** Synthesizes raw commit data into structured Engineering Experiences, dropping low-value noise and retaining high-signal architectural insights.
- **APM Telemetry Webhooks (Self-Correcting Graph):** Integrates directly with your observability stack. When a metric breaches, LORE-X autonomously degrades the failing architectural pattern in its memory graph (e.g., from `VERIFIED` to `CONDITIONALLY_VALID` or `FAILED`).
- **3D Glassmorphism UI:** A sleek, premium dark-mode dashboard with a 3D animated dot-wave physics engine and interactive Mermaid.js lineage graphs.

## Quickstart

Bootstrap your LORE-X architectural memory engine in four simple commands:

```bash
# 1. Install dependencies via uv
uv sync

# 2. Initialize the database and background Git hooks
lorex init

# 3. Ingest your historical commits
lorex ingest .

# 4. Launch the web dashboard
lorex serve
```

## License

This project is released under the [MIT License](LICENSE).
