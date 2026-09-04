import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from lorex.db.schema import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lorex.db")

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

# Enable WAL mode for SQLite for better concurrent read/write performance
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def init_db():
    """Creates all tables defined in Base metadata."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Returns a raw SessionLocal instance for scripts and tests."""
    return SessionLocal()

def get_db():
    """FastAPI dependency generator yielding a session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
