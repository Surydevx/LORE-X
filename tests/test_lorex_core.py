import uuid
from datetime import datetime, timezone
from lorex.core.models import ExperienceTuple, StatusEnum
from lorex.core.graph import detect_cycles
from lorex.core.metrics import CarbonMetrics
from lorex.db.schema import Base, Project, Experience
from lorex.db.session import engine, get_session, init_db
from lorex.engine.revision import RevisionEngine

def test_experience_tuple_serialization():
    data = {
        "id": "123",
        "problem": "test problem",
        "action": "test action",
        "conditions": ["cond1", "cond2"],
        "evidence": ["ev1"],
        "outcome": "test outcome",
        "status": StatusEnum.VERIFIED,
        "confidence": 0.9,
        "source_id": "src1",
        "source_type": "discussion"
    }
    
    t = ExperienceTuple(**data)
    assert t.id == "123"
    assert t.status == StatusEnum.VERIFIED
    
    dumped = t.model_dump()
    assert dumped["id"] == "123"
    assert "created_at" in dumped
    assert "valid_from" in dumped

def test_detect_cycles():
    # 1 -> 2 -> 3 -> 1
    depends_map = {
        1: {2},
        2: {3},
        3: {1}
    }
    id_set = {1, 2, 3}
    cycles = detect_cycles(depends_map, id_set)
    assert len(cycles) > 0
    # The cycle could be [1, 2, 3, 1], [2, 3, 1, 2], etc.
    assert any(set(c) == {1, 2, 3} for c in cycles)

def test_carbon_metrics():
    # Parse savings
    savings, cost = CarbonMetrics.parse_carbon("~ 500 kWh saved")
    assert savings == 500.0
    assert cost == 0.0
    
    # Parse cost
    savings, cost = CarbonMetrics.parse_carbon("100 kWh cost increase")
    assert savings == 0.0
    assert cost == 100.0
    
    impact = CarbonMetrics.calculate_impact(500.0, 100.0)
    assert impact["net_kwh"] == 400.0
    assert impact["co2_kg_month"] == 160.0
    
def test_revision_engine():
    init_db()
    session = get_session()
    
    try:
        p = session.query(Project).filter_by(id="p1").first()
        if not p:
            p = Project(id="p1", name="Test Project")
            session.add(p)
        
        now = datetime.now(timezone.utc)
        e1 = Experience(
            id="e1",
            project_id="p1",
            problem="prob",
            action="act",
            conditions=["a", "b"],
            outcome="success",
            status="PARTIALLY_VERIFIED",
            confidence=0.8,
            created_at=now,
            valid_from=now
        )
        session.add(e1)
        session.commit()
        
        engine = RevisionEngine()
        
        # Test VERIFIED
        updated_e = engine.record_outcome("e1", "success", ["a", "b"], session)
        assert updated_e.id == "e1"
        assert updated_e.status == "VERIFIED"
        
        # Test CONDITIONALLY_VALID
        new_e = engine.record_outcome("e1", "success", ["a", "c"], session)
        assert new_e.id != "e1"
        assert new_e.status == "CONDITIONALLY_VALID"
        
        old_e = session.query(Experience).filter_by(id="e1").first()
        assert old_e.status == "SUPERSEDED"
        assert old_e.superseded_by == new_e.id
        assert old_e.valid_until is not None
        
        # Test FAILED
        fail_e = engine.record_outcome(new_e.id, "failure", ["a", "c"], session)
        assert fail_e.id != new_e.id
        assert fail_e.status == "FAILED"
        
        new_e_updated = session.query(Experience).filter_by(id=new_e.id).first()
        assert new_e_updated.status == "SUPERSEDED"
        
    finally:
        # Teardown
        Base.metadata.drop_all(bind=session.get_bind())
        session.close()
