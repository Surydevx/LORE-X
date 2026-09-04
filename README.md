# LORE-X: Living Organizational Record Engine

LORE-X is an autonomous, self-correcting architectural memory engine. By passively monitoring your engineering workflow via Git hooks, it tracks your team's decisions, extracts the intent using Large Language Models, and maps them into a robust mathematical tuple: $(P, A, C, V, O, T, S)$.

When integrated with your observability stack (APM), LORE-X continuously validates these historical decisions against live production telemetry—automatically degrading the confidence of patterns that fail at scale.

---

## 🧠 The Mathematical Model

LORE-X models every architectural decision as a 7-dimensional tuple:

- **$P$ (Problem)**: The engineering challenge or bottleneck (e.g., *API latency spikes under load*).
- **$A$ (Action)**: The specific architectural decision applied (e.g., *Implemented Redis connection pooling*).
- **$C$ (Conditions)**: The operational boundaries where this action is valid (e.g., *< 10k concurrent users*).
- **$V$ (Evidence)**: Empirical data backing the decision (commit hashes, pull requests, APM logs).
- **$O$ (Outcome)**: The observed result of the action (e.g., *Latency reduced by 35%*).
- **$T$ (Temporal Validity)**: The lifespan of the decision (from deployment until superseded).
- **$S$ (Status)**: The current health of the decision (`VERIFIED`, `PARTIALLY_VERIFIED`, `CONDITIONALLY_VALID`, `SUPERSEDED`, or `FAILED`).

---

## ⚡ Core Features

- **Zero-Touch Git Integration**: Automatically intercepts and ingests `git commit` logs in the background without altering developer workflow.
- **Hybrid Retrieval Engine**: When querying past decisions, LORE-X uses a weighted hybrid algorithm prioritizing Semantic Relevance, Graph Lineage (Modernity), Temporal Validity, and Operational Outcome.
- **Self-Correcting Memory Graph (APM Webhooks)**: Exposes a secure webhook endpoint for your telemetry stack (Datadog, New Relic, Prometheus). When an incident occurs, LORE-X autonomously traverses the graph and downgrades the offending architectural pattern.
- **Idempotent Ingestion**: Safely run and re-run repository syncs; LORE-X guarantees exact-once processing of commit hashes to prevent database bloat.
- **Premium Visualization**: A sleek, dark-mode 3D glassmorphism dashboard featuring an interactive Mermaid.js lineage graph and particle physics.

---

## 🛠️ Installation & Quickstart

LORE-X is distributed as a standalone, statically linked PyInstaller binary. No language runtimes or external dependencies are required.

### 1. Install the Binary
```bash
# Download the binary (example)
chmod +x lorex
sudo mv lorex /usr/local/bin/
```

### 2. Initialize a Repository
Navigate to the root of your Git repository and initialize LORE-X. This creates the local SQLite database and installs the necessary Git `post-commit` hooks.
```bash
cd /path/to/your/repo
lorex init
```
*Note: During initialization, you will be prompted for an LLM API key (Gemini, OpenAI, or Anthropic).*

### 3. Backfill Historical Data
Ingest your repository's existing history. The engine will batch process commits, intelligently ignoring typos, formatting, and linting commits.
```bash
lorex ingest . --limit 50
```

### 4. Launch the Dashboard
Start the local server to explore the generated architectural memory graph.
```bash
lorex serve --port 8000
```
Open your browser to `http://localhost:8000/dashboard`.

---

## 🔌 APM Webhook Integration

To enable the self-correcting graph, point your APM alerting system (e.g., PagerDuty, Datadog) to the LORE-X webhook endpoint.

**Endpoint:** `POST http://<lorex-host>:8000/api/outcomes/apm-webhook`

**Headers:**
```http
Content-Type: application/json
X-Lorex-Signature: sha256=<HMAC_HEX_SIGNATURE>
```
*Note: The signature must be generated using your `LOREX_WEBHOOK_SECRET` environment variable.*

**Payload:**
```json
{
  "alert_id": "inc-9923",
  "severity": "critical",
  "description": "Database connection pool exhausted",
  "affected_services": ["api-gateway"],
  "timestamp": "2026-09-04T12:00:00Z"
}
```

Upon receiving an alert, LORE-X will semantically match the failure description against its active architectural decisions and downgrade the relevant `VERIFIED` nodes to `FAILED` or `CONDITIONALLY_VALID`.

---

## 🔍 CLI Reference

| Command | Description |
|---|---|
| `lorex init` | Bootstraps the `.env` file, database schema, and `post-commit` hook. |
| `lorex ingest <path>` | Scans a Git repository and extracts architectural decisions. Accepts `--limit`. |
| `lorex query "text"` | Runs a CLI-based hybrid retrieval query against the memory graph. |
| `lorex serve` | Starts the Uvicorn ASGI server and hosts the interactive dashboard. |

---

## 🛡️ Security & Privacy

LORE-X is designed with a strict security-first posture:
- **Local Database**: All experiences, evidence, and graphs are stored strictly locally in `lorex.db`.
- **Sanitized Extraction**: LLM extraction is heavily constrained to output only JSON tuples.
- **XSS Protection**: The web dashboard employs rigorous HTML sanitization before rendering any user-supplied or LLM-generated data.
- **Sandboxed Execution**: Subprocess calls (like `git log`) use strict binary execution arrays to prevent shell injection vectors.

---

## License

This project is released under the [MIT License](LICENSE).
