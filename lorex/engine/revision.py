from datetime import datetime, timezone
import uuid
from typing import List
from lorex.db.schema import Experience

class RevisionEngine:
    def record_outcome(self, experience_id: str, observed_outcome: str, observed_conditions: List[str], session) -> Experience:
        experience = session.query(Experience).filter(Experience.id == experience_id).first()
        if not experience:
            raise ValueError(f"Experience {experience_id} not found")

        outcome_match = (observed_outcome.strip() == experience.outcome.strip())
        conditions_match = (set(observed_conditions) == set(experience.conditions))
        
        if outcome_match and conditions_match:
            experience.status = "VERIFIED"
            session.commit()
            return experience
        
        if outcome_match and not conditions_match:
            new_status = "CONDITIONALLY_VALID"
        else:
            new_status = "FAILED"
            
        now = datetime.now(timezone.utc)
        experience.valid_until = now
        experience.status = "SUPERSEDED"
        
        new_experience = Experience(
            id=str(uuid.uuid4()),
            project_id=experience.project_id,
            problem=experience.problem,
            action=experience.action,
            conditions=observed_conditions,
            outcome=observed_outcome,
            status=new_status,
            confidence=experience.confidence,
            created_at=experience.created_at,
            valid_from=now
        )
        
        experience.superseded_by = new_experience.id
        
        session.add(new_experience)
        session.commit()
        return new_experience
