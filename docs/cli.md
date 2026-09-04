---
icon: lucide/terminal
---

# CLI Guide

LORE-X ships a unified CLI via the `lorex` command. All commands are registered in `lorex/cli.py` and available after installation.

---

## `lorex init`

Bootstraps LORE-X in the current Git repository. This command is interactive and idempotent — it's safe to run multiple times.

**What it does:**

1. Checks that you're inside a Git repository (`.git/` must exist).
2. If no LLM API key is detected in the environment, prompts you to select a provider (Gemini, OpenAI, or Anthropic) and securely enter your key via hidden input.
3. Writes the key to a `.env` file in the current directory.
4. Adds `lorex.db` and `.env` to `.gitignore` (if not already present).
5. Creates the SQLite database and all tables.
6. Installs a `post-commit` Git hook that runs `lorex ingest . --limit 1` in the background after every commit.

```bash
cd /path/to/your/repo
lorex init
```

---

## `lorex ingest <path>`

Scans a Git repository's commit history, filters out trivial commits, and extracts architectural decisions using LLM analysis.

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `path` | `.` | Path to the Git repository to scan |
| `--limit` | `5` | Maximum number of recent commits to process |
| `--project` | `p1` | Project ID for namespace isolation |

**Behavior:**

- Loads the `.env` from the target repository path (if it exists), falling back to the current working directory's `.env`.
- Skips commits that have already been ingested (idempotent by commit hash).
- Drops trivial commits: messages under 30 characters or containing `lint`, `typo`, `bump`, `format`, or `merge`.
- Runs LLM extraction concurrently (up to 5 parallel) with per-thread database sessions.

```bash
# Ingest the last 20 commits from the current repo
lorex ingest . --limit 20

# Ingest from a specific path
lorex ingest /path/to/other/repo --limit 10 --project myproject
```

---

## `lorex query "<text>"`

Queries the architectural memory graph using the Hybrid Retrieval Engine. Returns the top-ranked experiences from the terminal.

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `text` | *(required)* | The problem or question to search for |
| `--project` | `p1` | Project ID to scope the query |

```bash
lorex query "database connection pooling strategy"
```

**Output:**
```
Results for 'database connection pooling strategy':
- [VERIFIED] Implemented Redis connection pooling with max 50 connections (Score: 1.87)
- [CONDITIONALLY_VALID] Switched to PgBouncer for connection management (Score: 1.42)
- [SUPERSEDED] Used naive per-request DB connections (Score: 0.39)
```

---

## `lorex log`

Displays a styled table of recent extractions in the terminal. Requires the `rich` package (installed automatically).

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--limit` | `10` | Number of recent experiences to display |
| `--project` | `p1` | Project ID to filter by |

```bash
lorex log --limit 5
```

**Output:**
```
┌─────────────────────────────────────────────────────────────┐
│              LORE-X Extraction History (p1)                 │
├─────────┬──────────┬────────────────────┬───────────────────┤
│ Commit  │  Status  │ Problem            │ Action            │
├─────────┼──────────┼────────────────────┼───────────────────┤
│ a1b2c3d │ VERIFIED │ API latency sp...  │ Implemented Re... │
│ e4f5g6h │ FAILED   │ Memory leak in...  │ Added object p... │
└─────────┴──────────┴────────────────────┴───────────────────┘
```

---

## `lorex graph`

Renders the knowledge graph as an interactive Rich tree in the terminal. Shows the Problem → Action → Context → Outcome hierarchy for each ingested commit.

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--limit` | `5` | Number of recent commits to include |
| `--project` | `p1` | Project ID to filter by |

```bash
lorex graph --limit 3
```

**Output:**
```
🧠 LORE-X Knowledge Graph (p1)
├── Commit a1b2c3d
│   └── Problem: API latency spikes under load
│       └── Action: Implemented Redis connection pooling
│           └── Outcome: Latency reduced by 35%
├── Commit e4f5g6h
│   └── Problem: Memory leak in worker process
│       └── Action: Added object pool with TTL eviction
│           └── Outcome: Memory usage stabilized
```

---

## `lorex serve`

Starts the Uvicorn ASGI server hosting the FastAPI application and web dashboard.

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--port` | `8000` | Port to bind the server to |

```bash
lorex serve --port 3000
```

The dashboard is accessible at `http://localhost:<port>/dashboard`. The API is available at `http://localhost:<port>/api/`.

> **Note:** `reload=False` is hardcoded to ensure compatibility with PyInstaller-bundled binaries.
