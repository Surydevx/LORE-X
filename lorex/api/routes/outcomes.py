from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from lorex.db.session import get_db
from lorex.engine.revision import RevisionEngine

router = APIRouter()

class OutcomeRequest(BaseModel):
    experience_id: str
    observed_outcome: str
    observed_conditions: List[str]

@router.post("")
def record_outcome(req: OutcomeRequest, session: Session = Depends(get_db)):
    engine = RevisionEngine()
    try:
        updated_exp = engine.record_outcome(
            req.experience_id, 
            req.observed_outcome, 
            req.observed_conditions, 
            session
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    return {
        "message": "Outcome recorded",
        "new_experience_id": updated_exp.id,
        "status": updated_exp.status
    }
