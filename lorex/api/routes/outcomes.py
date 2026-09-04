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

class APMAlert(BaseModel):
    incident_id: str
    breached_metric: str
    target_node_id: str
    auth_token: str = ""

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

@router.post("/apm-webhook")
def handle_apm_webhook(alert: APMAlert, session: Session = Depends(get_db)):
    # H13: Verify webhook authenticity via shared secret
    import os
    webhook_secret = os.getenv("LOREX_WEBHOOK_SECRET")
    if webhook_secret and not alert.auth_token:
        raise HTTPException(status_code=401, detail="Missing auth_token")
    if webhook_secret and alert.auth_token != webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid auth_token")
    
    engine = RevisionEngine()
    
    observed_outcome = f"APM Alert {alert.incident_id}: Breached {alert.breached_metric}"
    conditions = [f"metric_breach={alert.breached_metric}"]
    
    try:
        updated_exp = engine.record_outcome(
            alert.target_node_id,
            observed_outcome,
            conditions,
            session
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
        
    return {
        "message": "APM telemetry degradation handled and experience revised",
        "new_experience_id": updated_exp.id,
        "status": updated_exp.status
    }
