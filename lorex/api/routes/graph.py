from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

from lorex.db.session import get_db
from lorex.db.schema import Experience

router = APIRouter()

class NodeData(BaseModel):
    problem: str
    action: str
    conditions: List[str]
    outcome: str
    status: str
    confidence: float
    commit_hash: Optional[str]
    author: Optional[str]
    timestamp: Optional[datetime]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]

class Node(BaseModel):
    id: str
    type: str = "Experience"
    data: NodeData

class Edge(BaseModel):
    source: str
    target: str
    label: str

class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

def safe_isoformat(dt):
    if not dt:
        return None
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt.replace("Z", "+00:00")).isoformat()
        except ValueError:
            return dt
    return dt.isoformat()

@router.get("", response_model=GraphResponse)
def get_graph(
    project_id: str = Query("p1", description="Project ID to isolate graph"),
    session: Session = Depends(get_db)
):
    try:
        # H11 / Bug 7.2: project isolation
        experiences = session.query(Experience).filter(Experience.project_id == project_id).all()
        
        nodes = []
        edges = []
        
        existing_node_ids = {exp.id for exp in experiences}
        
        for exp in experiences:
            nodes.append({
                "id": exp.id,
                "type": "Experience",
                "data": {
                    "problem": exp.problem,
                    "action": exp.action,
                    "conditions": exp.conditions or [],
                    "outcome": exp.outcome,
                    "status": exp.status,
                    "confidence": exp.confidence,
                    "commit_hash": exp.commit_hash,
                    "author": exp.author,
                    "timestamp": safe_isoformat(exp.created_at),
                    "valid_from": safe_isoformat(exp.valid_from),
                    "valid_until": safe_isoformat(exp.valid_until)
                }
            })
            
            # Bug 7.1: Only add edge if target node exists in this graph
            if exp.superseded_by and exp.superseded_by in existing_node_ids:
                edges.append({
                    "source": exp.id,
                    "target": exp.superseded_by,
                    "label": "superseded_by"
                })
                
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
