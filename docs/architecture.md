# LORE-X Hybrid Retrieval Engine

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
- Baseline confidence is extracted during the ingestion phase (typically 0.8 to 0.95).
- Down-weighted if contradictory evidence has been recorded.

### 4. Graph Lineage Score ($S_{graph}$)
In LORE-X, experiences form a directed acyclic graph (DAG) via the `superseded_by` relationship.
- If a retrieved node is `SUPERSEDED`, the engine can follow the directed edge to retrieve the modern, valid descendant.

## Bayesian Optimization
The weights ($\alpha, \beta, \gamma, \delta$) are not hardcoded. LORE-X includes a Bayesian Optimization loop powered by **Optuna**.
By executing `python scripts/optimize.py`, operators can continually tune the multi-dimensional weights against a set of Benchmark Scenarios, maximizing the **F1 Score** of Recommendation Accuracy and Temporal Rejection Rate.
