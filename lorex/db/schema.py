from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    
    events: Mapped[List["EngineeringEvent"]] = relationship(back_populates="project")
    experiences: Mapped[List["Experience"]] = relationship(back_populates="project")

class EngineeringEvent(Base):
    __tablename__ = "engineering_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    source_type: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    author: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    
    project: Mapped["Project"] = relationship(back_populates="events")

class Experience(Base):
    __tablename__ = "experiences"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    problem: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    conditions: Mapped[List[str]] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    valid_from: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    superseded_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    project: Mapped["Project"] = relationship(back_populates="experiences")
    evidences: Mapped[List["Evidence"]] = relationship(back_populates="experience")
    embeddings: Mapped[List["Embedding"]] = relationship(back_populates="experience")

class Evidence(Base):
    __tablename__ = "evidences"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    experience_id: Mapped[str] = mapped_column(ForeignKey("experiences.id"))
    source_type: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    
    experience: Mapped["Experience"] = relationship(back_populates="evidences")

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    experience_id: Mapped[str] = mapped_column(ForeignKey("experiences.id"))
    
    vector: Mapped[List[float]] = mapped_column(JSON)
    
    experience: Mapped["Experience"] = relationship(back_populates="embeddings")
