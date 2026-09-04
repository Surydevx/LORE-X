---
icon: lucide/braces
---

# API Reference

LORE-X exposes a REST API via FastAPI. When running `lorex serve`, all endpoints are available at `http://localhost:8000/api/`.

---

## Event Ingestion

### `POST /api/events`

Ingest a single engineering event and immediately extract an Experience Tuple from it.

**Request Body:**
```json
{
  "project_id": "p1",
  "source_type": "commit",
  "source_id": "abc123def456",
  "author": "alice",
  "content": "Refactored the connection pool to use async context managers with TTL-based eviction"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | Yes | Project namespace for isolation |
| `source_type` | string | Yes | Type of source event (e.g., `commit`, `pr`, `incident`) |
| `source_id` | string | Yes | Unique identifier for the source (e.g., commit hash) |
| `author` | string | Yes | Author of the event |
| `content` | string | Yes | Raw content to extract from |

**Response (200):**
```json
{
  "message": "Event ingested",
  "experience_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### `POST /api/events/vcs/ingest-local`

Batch-ingest commits from a local Git repository. This is the API equivalent of `lorex ingest`.

**Request Body:**
```json
{
  "repo_path": "/path/to/repo",
  "project_id": "p1",
  "limit": 10
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repo_path` | string | *(required)* | Absolute path to the Git repository |
| `project_id` | string | *(required)* | Project namespace |
| `limit` | integer | `10` | Maximum commits to process |

**Response (200):**
```json
{
  "message": "Successfully ingested 7 experiences from /path/to/repo"
}
```

**Response (500):**
```json
{
  "detail": "VCS ingestion failed: Failed to run git log in /bad/path: ..."
}
```

---

## Query

### `POST /api/query`

Run a hybrid retrieval query against the experience memory graph.

**Request Body:**
```json
{
  "query": "database connection pooling",
  "top_k": 5,
  "project_id": "p1"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | *(required, min 1 char)* | The problem or question to search for |
| `top_k` | integer | `5` | Number of results to return (1–100) |
| `project_id` | string | `"p1"` | Project namespace to scope the query |

**Response (200):**
```json
{
  "results": [
    {
      "id": "exp-uuid",
      "problem": "API latency spikes under load",
      "action": "Implemented Redis connection pooling",
      "conditions": ["< 10k concurrent users"],
      "outcome": "Latency reduced by 35%",
      "status": "VERIFIED",
      "confidence": 0.9,
      "commit_hash": "a1b2c3d",
      "author": "alice",
      "timestamp": "2024-09-01T12:00:00Z",
      "score": 1.87,
      "evidence": ["Extracted from abc123"]
    }
  ]
}
```

---

## Outcomes

### `POST /api/outcomes`

Record an observed outcome against an existing experience. This triggers the Revision Engine's self-correcting logic.

**Request Body:**
```json
{
  "experience_id": "exp-uuid",
  "observed_outcome": "Latency reduced by 35%",
  "observed_conditions": ["< 10k concurrent users"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `experience_id` | string | ID of the experience to validate |
| `observed_outcome` | string | The outcome actually observed |
| `observed_conditions` | string[] | The conditions under which the outcome was observed |

**Behavior:**

| Scenario | Result |
|----------|--------|
| Outcome + conditions match exactly | Status upgraded to `VERIFIED` |
| Outcome matches, conditions differ | Old → `SUPERSEDED`, new created as `CONDITIONALLY_VALID` |
| Outcome doesn't match | Old → `SUPERSEDED`, new created as `FAILED` |

**Response (200):**
```json
{
  "message": "Outcome recorded",
  "new_experience_id": "new-exp-uuid",
  "status": "CONDITIONALLY_VALID"
}
```

**Response (404):**
```json
{
  "detail": "Experience exp-uuid not found"
}
```

---

### `POST /api/outcomes/apm-webhook`

APM telemetry webhook endpoint for autonomous graph degradation. Connect this to your monitoring/alerting stack (Datadog, PagerDuty, Prometheus AlertManager).

**Request Body:**
```json
{
  "incident_id": "inc-9923",
  "breached_metric": "p99_latency_ms",
  "target_node_id": "exp-uuid",
  "auth_token": "your-webhook-secret"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `incident_id` | string | Yes | Unique incident identifier |
| `breached_metric` | string | Yes | The metric that was breached |
| `target_node_id` | string | Yes | Experience ID to degrade |
| `auth_token` | string | No | Must match `LOREX_WEBHOOK_SECRET` if set |

**Authentication:** If the `LOREX_WEBHOOK_SECRET` environment variable is set, the `auth_token` field is required and must match. Returns `401` if missing, `403` if invalid.

**Response (200):**
```json
{
  "message": "APM telemetry degradation handled and experience revised",
  "new_experience_id": "new-exp-uuid",
  "status": "FAILED"
}
```

---

## Graph

### `GET /api/graph`

Retrieve the full experience lineage graph as nodes and edges. Used by the dashboard for Mermaid.js visualization.

**Query Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `project_id` | `"p1"` | Project namespace to scope the graph |

**Response (200):**
```json
{
  "nodes": [
    {
      "id": "exp-uuid",
      "type": "Experience",
      "data": {
        "problem": "API latency spikes",
        "action": "Redis connection pooling",
        "conditions": ["< 10k users"],
        "outcome": "Latency reduced 35%",
        "status": "VERIFIED",
        "confidence": 0.9,
        "commit_hash": "a1b2c3d",
        "author": "alice",
        "timestamp": "2024-09-01T12:00:00",
        "valid_from": "2024-09-01T12:00:00",
        "valid_until": null
      }
    }
  ],
  "edges": [
    {
      "source": "old-exp-uuid",
      "target": "new-exp-uuid",
      "label": "superseded_by"
    }
  ]
}
```

---

## Utility

### `GET /health`

Health check endpoint.

**Response (200):**
```json
{
  "status": "ok"
}
```

### `GET /dashboard`

Redirects (HTTP 302) to `/static/index.html` — the interactive glassmorphism web dashboard.
