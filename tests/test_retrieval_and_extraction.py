from datetime import datetime, timezone
import pytest
from lorex.core.models import ExperienceTuple, StatusEnum
from lorex.db.schema import Base, Project, EngineeringEvent, Experience
from lorex.db.session import get_session, init_db
from lorex.engine.extraction import ExperienceExtractor
from lorex.engine.retrieval import HybridRetrievalEngine

@pytest.fixture
def session():
    init_db()
    sess = get_session()
    yield sess
    Base.metadata.drop_all(bind=sess.get_bind())
    sess.close()

def test_experience_extractor(session):
    extractor = ExperienceExtractor()
    now = datetime.now(timezone.utc)
    
    p = Project(id="p1", name="Proj")
    session.add(p)
    session.commit()
    
    event = EngineeringEvent(
        id="evt1",
        project_id="p1",
        source_type="commit",
        source_id="sha123",
        timestamp=now,
        author="alice",
        content="Fixed the bug"
    )
    
    # Mock extract
    tup = extractor.extract_from_event(event)
    assert tup.source_id == "sha123"
    assert tup.status == StatusEnum.VERIFIED
    
    # Persist
    exp = extractor.persist_experience(tup, "p1", session)
    assert exp.project_id == "p1"
    assert len(exp.evidences) == 1
    assert exp.evidences[0].content.startswith("Evidence")

def test_hybrid_retrieval(session):
    engine = HybridRetrievalEngine()
    now = datetime.now(timezone.utc)
    
    # Setup some experiences
    e1 = Experience(
        id="exp1", project_id="p1", problem="p1", action="a1", conditions=[], outcome="o1",
        status="VERIFIED", confidence=0.9, created_at=now, valid_from=now
    )
    e2 = Experience(
        id="exp2", project_id="p1", problem="p2", action="a2", conditions=[], outcome="o2",
        status="SUPERSEDED", confidence=0.5, created_at=now, valid_from=now, valid_until=now
    )
    e3 = Experience(
        id="exp3", project_id="p1", problem="p3", action="a3", conditions=[], outcome="o3",
        status="FAILED", confidence=0.8, created_at=now, valid_from=now
    )
    
    session.add_all([e1, e2, e3])
    session.commit()
    
    # Retrieve
    results = engine.retrieve("query", session, top_k=5)
    
    # Check ranking: e1 (VERIFIED) should be top, then e3 (FAILED), then e2 (SUPERSEDED)
    # due to temporal and outcome scoring.
    assert len(results) == 3
    assert results[0][0].id == "exp1"
    assert results[1][0].id == "exp3"
    assert results[2][0].id == "exp2"
