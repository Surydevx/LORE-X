# LORE-X Hybrid Retrieval Engine & Architecture

The core differentiator of LORE-X is its proprietary `HybridRetrievalEngine`. Instead of relying solely on vector similarity (Standard RAG), LORE-X dynamically calculates a unified confidence score $S_{total}$ using four distinct mathematical dimensions.

## Mathematical Formulation

The final ranking score is calculated as:

$$
S_{total} = \alpha \cdot S_{semantic} + \beta \cdot S_{graph} + \gamma \cdot S_{temporal} + \delta \cdot S_{outcome}
$$

### 1. Semantic Score ($S_{semantic}$)
Calculated using Cosine Similarity between the incoming query embedding and the historical Problem embedding.
- If embeddings are unavailable (e.g., offline mode), it falls back to a deterministic **Jaccard Lexical Token Overlap**.

### 2. Temporal Score ($S_{temporal}$)
Penalizes decisions that have exceeded their valid lifecycle.
- Active (`VERIFIED` or `CONDITIONALLY_VALID`): Multiplier of **1.0**.
- Obsolete (`SUPERSEDED` or `FAILED`): Heavy penalty multiplier (e.g., **0.1**).

### 3. Outcome Score ($S_{outcome}$)
Rewards decisions based on empirical evidence.
- Baseline confidence is extracted during the ingestion phase.
- Down-weighted if contradictory evidence has been recorded. This is entirely automated via the **APM Telemetry Webhook**, which directly modifies experience status upon observing metric degradation.

### 4. Graph Lineage Score ($S_{graph}$)
In LORE-X, experiences form a directed acyclic graph (DAG) via the `superseded_by` relationship.
- If a retrieved node is `SUPERSEDED`, the engine can follow the directed edge to retrieve the modern, valid descendant.

## Enterprise Ingestion & Automation

LORE-X achieves Zero-Touch integration:
- **Git Hook Automation:** `lorex init` binds a `post-commit` hook that silently ingests architectural decisions in the background.
- **Concurrency Throttling:** Background ingestion is protected by an `asyncio.Semaphore(5)` to prevent LLM API 429 Rate Limiting errors.
- **Heuristic Filtering:** Drops trivial commits (messages under 30 characters or matching patterns like 'lint', 'typo') to save extraction costs.
- **Cryptographic Provenance:** Captures explicit Git SHAs, author names, and timestamps for absolute traceability.

## Bayesian Optimization
The retrieval weights ($\alpha, \beta, \gamma, \delta$) are not hardcoded. LORE-X includes a Bayesian Optimization loop powered by **Optuna**.
By executing `python scripts/optimize.py`, operators can continually tune the multi-dimensional weights against a set of Benchmark Scenarios, maximizing the **F1 Score** of Recommendation Accuracy and Temporal Rejection Rate. The optimization engine strictly drops and rebuilds in-memory SQLite schema states per-trial to guarantee isolation.
