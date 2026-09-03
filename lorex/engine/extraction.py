import uuid
from typing import Optional
from datetime import datetime, timezone
from lorex.core.models import ExperienceTuple
from lorex.db.schema import EngineeringEvent, Experience, Evidence
from lorex.engine.llm import LLMClient

class ExperienceExtractor:
    def __init__(self, prompt_template_path: str = "lorex/prompts/extraction.jinja2"):
        self.prompt_template_path = prompt_template_path
        self.llm_client = LLMClient()

    def extract_from_event(self, event: EngineeringEvent, client=None) -> ExperienceTuple:
        # We can format the template here.
        prompt = f"Analyze event {event.id} with content: {event.content}"
        
        # Route through LLMClient
        tup = self.llm_client.generate_experience(
            prompt=prompt,
            event_id=event.id,
            source_type=event.source_type,
            source_id=event.source_id
        )
        return tup

    def persist_experience(self, tuple_data: ExperienceTuple, project_id: str, session) -> Experience:
        now = datetime.now(timezone.utc)
        exp = Experience(
            id=tuple_data.id,
            project_id=project_id,
            problem=tuple_data.problem,
            action=tuple_data.action,
            conditions=tuple_data.conditions,
            outcome=tuple_data.outcome,
            status=tuple_data.status.value,
            confidence=tuple_data.confidence,
            created_at=now,
            valid_from=now
        )
        session.add(exp)
        
        for ev in tuple_data.evidence:
            evidence_record = Evidence(
                id=str(uuid.uuid4()),
                experience_id=exp.id,
                source_type=tuple_data.source_type,
                source_id=tuple_data.source_id,
                content=ev,
                timestamp=now
            )
            session.add(evidence_record)
            
        session.commit()
        return exp
