from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from datetime import datetime

from lorex.db.session import get_db
from lorex.engine.retrieval import HybridRetrievalEngine
from lorex.db.schema import Experience

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=100)
    project_id: str = Field("p1", min_length=1)

class ExperienceResponse(BaseModel):
    id: str
    problem: str
    action: str
    conditions: List[str]
    outcome: str
    status: str
    confidence: float
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    score: float
    evidence: List[str]

class QueryResponse(BaseModel):
    results: List[ExperienceResponse]

@router.post("", response_model=QueryResponse)
def run_query(req: QueryRequest, session: Session = Depends(get_db)):
    try:
        engine = HybridRetrievalEngine()
        # The retrieval engine currently fetches all experiences without project filtering.
        # So we should filter them in the engine, but since the engine is just testing,
        # we can modify retrieval.py to filter if project_id is provided. For now, passing req.project_id might require changing retrieval.py.
        # Actually, in retrieval.py `session.query(Experience).all()` is called. Let's rely on that for now, 
        # or wait, I can just fetch them here? No, retrieval.py does it.
        # I'll update retrieval.py separately if needed.
        results = engine.retrieve(req.query, session, req.top_k, project_id=req.project_id)
        
        # Load evidences eagerly
        # Since retrieve() returns Experience objects, and we just added selectinload, we'd need it in retrieval.py.
        # But we can also query the IDs here.
        if not results:
            return {"results": []}
            
        exp_ids = [exp.id for exp, _ in results]
        
        # Reload with eager evidence loading to fix N+1
        experiences_with_evidence = session.query(Experience).options(
            selectinload(Experience.evidences)
        ).filter(Experience.id.in_(exp_ids)).all()
        
        exp_dict = {e.id: e for e in experiences_with_evidence}
        
        response_data = []
        for exp, score in results:
            loaded_exp = exp_dict.get(exp.id, exp)
            ev_content = [e.content for e in loaded_exp.evidences] if hasattr(loaded_exp, 'evidences') else []
            
            response_data.append({
                "id": exp.id,
                "problem": exp.problem,
                "action": exp.action,
                "conditions": exp.conditions or [],
                "outcome": exp.outcome,
                "status": exp.status,
                "confidence": exp.confidence,
                "commit_hash": exp.commit_hash,
                "author": exp.author,
                "timestamp": exp.created_at,
                "score": score,
                "evidence": ev_content
            })
            
        return {"results": response_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
