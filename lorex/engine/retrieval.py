import math
import re
from datetime import datetime, timezone
from typing import List, Tuple
from sqlalchemy.orm import Session
from lorex.db.schema import Experience, Embedding

class HybridRetrievalEngine:
    def __init__(
        self,
        alpha: float = 0.352,  # Semantic weight
        beta: float = 0.649,   # Graph topology weight
        gamma: float = 0.660,  # Temporal validity weight
        delta: float = 0.736   # Outcome status weight
    ):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        min_len = min(len(v1), len(v2))
        dot_product = sum(v1[i] * v2[i] for i in range(min_len))
        norm1 = math.sqrt(sum(x * x for x in v1[:min_len]))
        norm2 = math.sqrt(sum(x * x for x in v2[:min_len]))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        denom = norm1 * norm2
        if denom < 1e-300:
            return 0.0
        return dot_product / denom

    def _compute_lexical_similarity(self, query: str, experience) -> float:
        # Combine problem, action, and condition keywords
        problem = experience.problem or ""
        action = experience.action or ""
        conditions = experience.conditions or []
        # Guard against non-string elements in conditions
        cond_str = " ".join(str(c) for c in conditions)
        target_text = f"{problem} {action} {cond_str}".lower()
        query_tokens = set(re.findall(r"\w+", (query or "").lower()))
        target_tokens = set(re.findall(r"\w+", target_text))
        
        if not query_tokens or not target_tokens:
            return 0.0
        
        # True Jaccard similarity: |A ∩ B| / |A ∪ B|
        intersection = query_tokens & target_tokens
        union = query_tokens | target_tokens
        return len(intersection) / len(union)

    def _score_semantic(self, query: str, exp: Experience, session) -> float:
        # Get embedding for exp
        emb = session.query(Embedding).filter(Embedding.experience_id == exp.id).first()
        if not emb or not emb.vector:
            # No embedding stored — fall back to lexical similarity
            return self._compute_lexical_similarity(query, exp)
            
        # NOTE: Real query embedding not yet implemented.
        # Until an embedding model is wired in, use lexical similarity for scoring.
        return self._compute_lexical_similarity(query, exp)

    def _score_graph(self, exp: Experience, session) -> float:
        # Basic DAG lineage scoring via superseded_by relationships
        if exp.superseded_by:
            # This node has been superseded — penalize it
            return 0.2
        # Check if this node supersedes others (it's the latest in its chain)
        predecessors = session.query(Experience).filter(Experience.superseded_by == exp.id).count()
        if predecessors > 0:
            # This is a modern descendant — boost it
            return 0.8
        return 0.5

    def _score_temporal(self, exp: Experience) -> float:
        # 1.0 for currently active, penalizing expired or superseded entries
        if exp.status == "FAILED":
            return 0.5
        if exp.status == "SUPERSEDED":
            return 0.1
        if exp.valid_until is not None:
            try:
                now = datetime.now(timezone.utc)
                # Handle both naive and aware datetimes
                valid_until = exp.valid_until
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                if valid_until < now:
                    return 0.2  # Actually expired
            except (AttributeError, TypeError):
                pass
        return 1.0

    def _score_outcome(self, exp: Experience) -> float:
        status_weights = {
            "VERIFIED": 1.0,
            "PARTIALLY_VERIFIED": 0.7,
            "CONDITIONALLY_VALID": 0.6,
            "FAILED": 0.1,
            "SUPERSEDED": 0.05
        }
        return status_weights.get(exp.status, 0.5)

    def retrieve(self, query: str, session, top_k: int = 5, project_id: str = "p1") -> List[Tuple[Experience, float]]:
        if not query:
            return []
        # Clamp top_k to reasonable bounds
        top_k = max(1, min(top_k, 500))
        
        experiences = session.query(Experience).filter(Experience.project_id == project_id).all()
        
        scored = []
        for exp in experiences:
            s_sem = self._score_semantic(query, exp, session)
            s_gra = self._score_graph(exp, session)
            s_tem = self._score_temporal(exp)
            s_out = self._score_outcome(exp)
            
            total_score = (
                self.alpha * s_sem +
                self.beta * s_gra +
                self.gamma * s_tem +
                self.delta * s_out
            )
            scored.append((exp, total_score))
            
        # Sort by total score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
