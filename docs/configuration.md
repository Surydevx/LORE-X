---
icon: lucide/sliders
---

# Configuration

LORE-X reads configuration from environment variables. These can be set directly in your shell or loaded from a `.env` file.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | One of three | — | Google AI Studio API key. Highest priority provider. |
| `OPENAI_API_KEY` | One of three | — | OpenAI API key. Second priority. |
| `ANTHROPIC_API_KEY` | One of three | — | Anthropic API key. Third priority. |
| `DATABASE_URL` | No | `sqlite:///lorex.db` | SQLAlchemy database connection URL. |
| `LOREX_WEBHOOK_SECRET` | No | — | Shared secret for APM webhook authentication. |

At least one LLM API key is required for extraction to work. If none is available, LORE-X falls back to a degraded heuristic extraction from commit messages.

---

## Provider Priority

When multiple API keys are present, LORE-X selects the provider in this order:

1. **Gemini** (`GEMINI_API_KEY`) → model: `gemini/gemini-3.6-flash`
2. **OpenAI** (`OPENAI_API_KEY`) → model: `gpt-4o-mini`
3. **Anthropic** (`ANTHROPIC_API_KEY`) → model: `claude-3-haiku-20240307`

The Gemini and OpenAI providers request structured JSON output via `response_format: json_object`. Anthropic does not support this parameter, so it is omitted.

---

## `.env` File Handling

LORE-X has a two-layer `.env` loading strategy:

### CLI Layer (`lorex/cli.py`)

At CLI startup, `python-dotenv`'s `load_dotenv()` is called with `override=True`, loading from `<cwd>/.env`. This ensures all subsequent imports and module-level code can see the keys.

During `lorex ingest <path>`, the `.env` from the **target repository path** takes precedence over the current working directory:

```python
repo_env = Path(args.repo_path).resolve() / ".env"
if repo_env.exists():
    load_dotenv(dotenv_path=repo_env, override=True)
```

### Engine Layer (`lorex/engine/llm.py`)

The `LLMClient.__init__` also contains a manual `.env` parser as a safety net for environments where `python-dotenv` isn't available (e.g., inside a PyInstaller binary). It:

- Reads `<cwd>/.env` line by line
- Skips empty lines and comments (`#`)
- Splits on the first `=`
- Strips surrounding single/double quotes from values
- Only sets keys that aren't already in `os.environ` (so `load_dotenv` values take precedence)

### `lorex init`

The `init` command will prompt for an API key if none is detected, and writes it to `.env` in the current directory. It also:

- Reloads `.env` via `load_dotenv(override=True)` after writing
- Sets the key in `os.environ` for immediate use
- Ensures `.env` appears in `.gitignore`

---

## Database Configuration

The default SQLite database (`lorex.db`) is created in the current working directory. To use a different database:

```bash
export DATABASE_URL="sqlite:///path/to/custom.db"
# or for PostgreSQL:
export DATABASE_URL="postgresql://user:pass@localhost/lorex"
```

### SQLite-Specific Settings

When using SQLite, LORE-X applies:

- **WAL mode** (`PRAGMA journal_mode=WAL`) for concurrent read/write performance
- `check_same_thread=False` for multi-threaded async access
- `timeout=30` seconds for lock acquisition
- `pool_pre_ping=True` for connection health checks
- `expire_on_commit=False` for `asyncio.to_thread` compatibility
