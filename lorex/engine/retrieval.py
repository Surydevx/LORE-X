import math
import re
from typing import List, Tuple
from lorex.db.schema import Experience, Embedding

class HybridRetrievalEngine:
    def __init__(self, alpha: float = 0.4, beta: float = 0.2, gamma: float = 0.2, delta: float = 0.2):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        dot_product = sum(x * y for x, y in zip(v1, v2))
        norm1 = math.sqrt(sum(x * x for x in v1))
        norm2 = math.sqrt(sum(x * x for x in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _compute_lexical_similarity(self, query: str, experience) -> float:
        # Combine problem, action, and condition keywords
        target_text = f"{experience.problem} {experience.action} {' '.join(experience.conditions or [])}".lower()
        query_tokens = set(re.findall(r"\w+", query.lower()))
        target_tokens = set(re.findall(r"\w+", target_text))
        
        if not query_tokens or not target_tokens:
            return 0.0
        
        # Jaccard / token overlap
        intersection = query_tokens & target_tokens
        return len(intersection) / len(query_tokens)

    def _score_semantic(self, query: str, exp: Experience, session) -> float:
        # Get embedding for exp
        emb = session.query(Embedding).filter(Embedding.experience_id == exp.id).first()
        if not emb or not emb.vector:
            return self._compute_lexical_similarity(query, exp)
            
        # Mock query embedding
        query_embedding = [0.1] * len(emb.vector)
        return self._cosine_similarity(query_embedding, emb.vector)

    def _score_graph(self, exp: Experience) -> float:
        # Mock structural connectivity score
        return 0.5

    def _score_temporal(self, exp: Experience) -> float:
        # 1.0 for currently active, penalizing expired or superseded entries
        if exp.status == "SUPERSEDED" or exp.valid_until is not None:
            return 0.2
        return 1.0

    def _score_outcome(self, exp: Experience) -> float:
        # VERIFIED = 1.0, CONDITIONALLY_VALID = 0.6, FAILED = 0.1, SUPERSEDED = 0.05
        status_weights = {
            "VERIFIED": 1.0,
            "CONDITIONALLY_VALID": 0.6,
            "FAILED": 0.1,
            "SUPERSEDED": 0.05
        }
        return status_weights.get(exp.status, 0.5)

    def retrieve(self, query: str, session, top_k: int = 5) -> List[Tuple[Experience, float]]:
        experiences = session.query(Experience).all()
        
        scored = []
        for exp in experiences:
            s_sem = self._score_semantic(query, exp, session)
            s_gra = self._score_graph(exp)
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
