from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class StatusEnum(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CONDITIONALLY_VALID = "CONDITIONALLY_VALID"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"

class ExperienceTuple(BaseModel):
    id: str
    problem: str
    action: str
    conditions: List[str]
    evidence: List[str]
    outcome: str
    status: StatusEnum
    confidence: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
    superseded_by: Optional[str] = None
    source_id: str
    source_type: str
