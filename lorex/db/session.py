import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lorex.db.schema import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lorex.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def init_db():
    """Creates all tables defined in Base metadata."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Returns a raw SessionLocal instance for scripts and tests."""
    return SessionLocal()

def get_db():
    """FastAPI dependency generator yielding a session and closing it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
