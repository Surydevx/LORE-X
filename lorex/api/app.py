from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from lorex.db.session import init_db
from lorex.api.routes import events, query, outcomes, graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="LORE-X API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(outcomes.router, prefix="/api/outcomes", tags=["Outcomes"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/dashboard")
def get_dashboard():
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}
