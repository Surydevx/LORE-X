from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lorex.db.session import get_db
from lorex.db.schema import Experience

router = APIRouter()

@router.get("")
def get_graph(session: Session = Depends(get_db)):
    experiences = session.query(Experience).all()
    
    nodes = []
    edges = []
    
    for exp in experiences:
        nodes.append({
            "id": exp.id,
            "type": "Experience",
            "data": {
                "problem": exp.problem,
                "action": exp.action,
                "outcome": exp.outcome,
                "status": exp.status,
                "confidence": exp.confidence,
                "valid_from": exp.valid_from.isoformat() if exp.valid_from else None,
                "valid_until": exp.valid_until.isoformat() if exp.valid_until else None
            }
        })
        
        if exp.superseded_by:
            edges.append({
                "source": exp.id,
                "target": exp.superseded_by,
                "label": "superseded_by"
            })
            
    return {"nodes": nodes, "edges": edges}
