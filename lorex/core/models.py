from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class StatusEnum(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONDITIONALLY_VALID = "CONDITIONALLY_VALID"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"

class ExperienceTuple(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: str = Field(..., min_length=1)
    project_id: str = Field(default="p1", min_length=1)
    problem: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    conditions: List[str]
    evidence: List[str]
    outcome: str = Field(..., min_length=1)
    status: StatusEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
    superseded_by: Optional[str] = None
    
    # Missing fields in models.py that are present in schema.py
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    
    source_id: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
