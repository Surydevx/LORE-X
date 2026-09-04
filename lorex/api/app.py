from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from lorex.db.session import init_db
from lorex.api.routes import events, query, outcomes, graph

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # Clean up database resources
    from lorex.db.session import engine
    engine.dispose()

app = FastAPI(title="LORE-X API", version="1.0.0", lifespan=lifespan)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred."}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request parameters."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(outcomes.router, prefix="/api/outcomes", tags=["Outcomes"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])

import sys
from pathlib import Path

def get_asset_path(relative_path: str) -> Path:
    """Resolves paths for both local development and PyInstaller bundled environments."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Navigate up if needed based on where this function lives vs the project root,
    # or treat base_path as the root if sys._MEIPASS is active.
    if hasattr(sys, '_MEIPASS'):
        return Path(base_path) / relative_path
    else:
        # Assuming the caller file is inside lorex/api/ or lorex/engine/
        return (Path(base_path).parent.parent / relative_path).resolve()

static_dir = str(get_asset_path("lorex/api/static"))
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/dashboard")
def get_dashboard():
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}
