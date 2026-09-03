from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from lorex.db.session import get_db
from lorex.engine.retrieval import HybridRetrievalEngine
from lorex.db.schema import Evidence

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("")
def run_query(req: QueryRequest, session: Session = Depends(get_db)):
    engine = HybridRetrievalEngine()
    results = engine.retrieve(req.query, session, req.top_k)
    
    response_data = []
    for exp, score in results:
        evidences = session.query(Evidence).filter_by(experience_id=exp.id).all()
        ev_content = [e.content for e in evidences]
        
        response_data.append({
            "id": exp.id,
            "problem": exp.problem,
            "action": exp.action,
            "conditions": exp.conditions,
            "outcome": exp.outcome,
            "status": exp.status,
            "confidence": exp.confidence,
            "commit_hash": exp.commit_hash,
            "author": exp.author,
            "score": score,
            "evidence": ev_content
        })
        
    return {"results": response_data}
