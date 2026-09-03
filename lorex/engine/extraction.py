import os
import sys
import uuid
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from lorex.core.models import ExperienceTuple
from lorex.db.schema import EngineeringEvent, Experience, Evidence
from lorex.engine.llm import LLMClient

if getattr(sys, 'frozen', False):
    # PyInstaller temporary extraction directory
    BASE_DIR = Path(sys._MEIPASS) / "lorex"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

PROMPTS_DIR = BASE_DIR / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))
class ExperienceExtractor:
    def __init__(self, prompt_template_path: str = "extraction.jinja2"):
        self.prompt_template_path = prompt_template_path
        self.llm_client = LLMClient()
        self.template = jinja_env.get_template(self.prompt_template_path)

    def extract_from_event(self, event: EngineeringEvent, client=None) -> ExperienceTuple:
        # We can format the template here.
        prompt = self.template.render(event=event)
        
        try:
            # Route through LLMClient
            tup = self.llm_client.generate_experience(
                prompt=prompt,
                event_id=event.id,
                source_type=event.source_type,
                source_id=event.source_id
            )
            return tup
        except Exception as e:
            print(f"[LORE-X ERROR] LLM Extraction failed for commit {event.commit_hash[:7] if event.commit_hash else 'unknown'}: {str(e)}")
            from lorex.core.models import StatusEnum
            
            lines = event.content.strip().split("\n")
            subject_line = "Unknown Action"
            for line in lines:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("commit ") and not clean_line.startswith("AuthorName:") and not clean_line.startswith("AuthorEmail:") and not clean_line.startswith("Date:") and not clean_line.startswith("diff "):
                    subject_line = clean_line
                    break
                    
            return ExperienceTuple(
                id=str(uuid.uuid4()),
                problem="LLM extraction failed. Raw commit body: " + event.content,
                action=subject_line[:100],
                conditions=["Extraction degraded"],
                evidence=[f"Commit {event.commit_hash[:7] if event.commit_hash else 'unknown'} by {event.author_name or 'developer'}"],
                outcome="Unknown (LLM Failure)",
                status=StatusEnum.VERIFIED,
                confidence=0.1,
                source_id=event.source_id,
                source_type=event.source_type
            )

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
