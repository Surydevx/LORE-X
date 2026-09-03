from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from lorex.db.session import get_db
from lorex.db.schema import EngineeringEvent, Project
from lorex.engine.extraction import ExperienceExtractor
from sqlalchemy.orm import Session

router = APIRouter()

class EventIngestRequest(BaseModel):
    project_id: str
    source_type: str
    source_id: str
    author: str
    content: str

@router.post("")
def ingest_event(req: EventIngestRequest, session: Session = Depends(get_db)):
    # Ensure project exists
    project = session.query(Project).filter_by(id=req.project_id).first()
    if not project:
        project = Project(id=req.project_id, name=f"Project {req.project_id}")
        session.add(project)
        session.commit()

    event = EngineeringEvent(
        id=str(uuid.uuid4()),
        project_id=req.project_id,
        source_type=req.source_type,
        source_id=req.source_id,
        timestamp=datetime.utcnow(),
        author=req.author,
        content=req.content
    )
    session.add(event)
    session.commit()

    extractor = ExperienceExtractor()
    tup = extractor.extract_from_event(event)
    exp = extractor.persist_experience(tup, req.project_id, session)

    return {"message": "Event ingested", "experience_id": exp.id}

from lorex.vcs.local_git import GitLogIngester

class VCSRequest(BaseModel):
    repo_path: str
    project_id: str
    limit: int = 10

@router.post("/vcs/ingest-local")
async def ingest_local_git(req: VCSRequest, session: Session = Depends(get_db)):
    ingester = GitLogIngester()
    try:
        exps = await ingester.ingest_repository(req.repo_path, req.project_id, session, req.limit)
        return {"message": f"Successfully ingested {len(exps)} experiences from {req.repo_path}"}
    except Exception as e:
        return {"error": str(e)}
