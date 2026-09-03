import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from lorex.api.app import app
from lorex.db.schema import Base, Project
from lorex.db.session import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as session:
        if not session.query(Project).filter_by(id="p1").first():
            session.add(Project(id="p1", name="Test Project"))
            session.commit()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ingest_event():
    response = client.post("/api/events", json={
        "project_id": "p1",
        "source_type": "commit",
        "source_id": "commit123",
        "author": "dev",
        "content": "Did some work"
    })
    assert response.status_code == 200
    data = response.json()
    assert "experience_id" in data

def test_run_query():
    client.post("/api/events", json={
        "project_id": "p1",
        "source_type": "commit",
        "source_id": "commit123",
        "author": "dev",
        "content": "Did some work"
    })
    
    response = client.post("/api/query", json={"query": "test", "top_k": 2})
    assert response.status_code == 200
    assert "results" in response.json()
    assert len(response.json()["results"]) > 0

def test_record_outcome():
    res = client.post("/api/events", json={
        "project_id": "p1",
        "source_type": "commit",
        "source_id": "commit123",
        "author": "dev",
        "content": "Did some work"
    })
    e_id = res.json()["experience_id"]
    
    response = client.post("/api/outcomes", json={
        "experience_id": e_id,
        "observed_outcome": "Failed outcome",
        "observed_conditions": ["high load"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Outcome recorded"
    assert data["new_experience_id"] != e_id

def test_get_graph():
    client.post("/api/events", json={
        "project_id": "p1",
        "source_type": "commit",
        "source_id": "commit123",
        "author": "dev",
        "content": "Did some work"
    })
    
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
