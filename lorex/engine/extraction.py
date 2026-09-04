import sys
import uuid
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound

from lorex.core.models import ExperienceTuple, StatusEnum
from lorex.db.schema import EngineeringEvent, Experience, Evidence
from lorex.engine.llm import LLMClient

import os
def get_asset_path(relative_path: str) -> Path:
    """Resolves paths for both local development and PyInstaller bundled environments."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if hasattr(sys, '_MEIPASS'):
        return Path(base_path) / relative_path
    else:
        return (Path(base_path).parent.parent / relative_path).resolve()

PROMPTS_DIR = str(get_asset_path("lorex/prompts"))

# Graceful Jinja2 environment setup — fall back to inline template if directory missing
_FALLBACK_TEMPLATE = """You are an expert software engineer analyzing an engineering event.
Extract the experience as a JSON object with: problem, action, conditions, outcome, status.

Event Type: {{ event.source_type }}
Event ID: {{ event.source_id }}
Author: {{ event.author }}

Content:
{{ event.content }}

Return valid JSON matching the ExperienceTuple schema."""

try:
    jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))
    # Test that the template actually exists
    jinja_env.get_template("extraction.jinja2")
except (TemplateNotFound, Exception):
    from jinja2 import DictLoader
    jinja_env = Environment(loader=DictLoader({"extraction.jinja2": _FALLBACK_TEMPLATE}))


class ExperienceExtractor:
    def __init__(self, prompt_template_path: str = "extraction.jinja2"):
        self.prompt_template_path = prompt_template_path
        self.llm_client = LLMClient()
        self.template = jinja_env.get_template(self.prompt_template_path)

    def extract_from_event(self, event: EngineeringEvent, client=None) -> ExperienceTuple:
        # Use injected client if provided, otherwise use self.llm_client
        llm = client if client is not None else self.llm_client
        
        # Render the prompt template
        prompt = self.template.render(event=event)
        
        try:
            tup = llm.generate_experience(
                prompt=prompt,
                event_id=event.id,
                source_type=event.source_type,
                source_id=event.source_id
            )
            return tup
        except Exception as e:
            # Null-guard event.content
            content = event.content or ""
            commit_hash = getattr(event, 'commit_hash', None)
            commit_hash = commit_hash[:7] if commit_hash else "unknown"
            author = getattr(event, 'author_name', None) or "developer"
            
            print(f"[LORE-X ERROR] LLM Extraction failed for commit {commit_hash}: {str(e)}", file=sys.stderr)
            
            lines = content.strip().split("\n") if content.strip() else []
            subject_line = "Unknown Action"
            for line in lines:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("commit ") and not clean_line.startswith("AuthorName:") and not clean_line.startswith("AuthorEmail:") and not clean_line.startswith("Date:") and not clean_line.startswith("diff "):
                    subject_line = clean_line
                    break
            
            # Truncate raw commit body to prevent DB bloat
            truncated_body = content[:500] + ("..." if len(content) > 500 else "")
                    
            return ExperienceTuple(
                id=str(uuid.uuid4()),
                problem=f"LLM extraction failed. Raw commit body: {truncated_body}",
                action=subject_line[:100],
                conditions=["Extraction degraded"],
                evidence=[f"Commit {commit_hash} by {author}"],
                outcome="Unknown (LLM Failure)",
                status=StatusEnum.PARTIALLY_VERIFIED,
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
            status=tuple_data.status.value if hasattr(tuple_data.status, 'value') else tuple_data.status,
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
            
        # NOTE: Caller is responsible for session.commit() to allow atomic batch operations
        session.flush()
        return exp
