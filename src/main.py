from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config import DATABASE_URL, DEBUG
from src.database import Database
from src.routes import events, inbox, subscriptions

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TriggersAPI",
    description="A unified RESTful interface for event ingestion, persistence, and delivery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database singleton
_db: Database | None = None


def get_database() -> Database:
    global _db
    if _db is None:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        _db = Database(db_path=db_path)
    return _db


def set_database(db: Database) -> None:
    """Allow overriding database (for testing)."""
    global _db
    _db = db


# Include API routes
app.include_router(events.router, prefix="/api/v1")
app.include_router(inbox.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")

# Mount static files
with contextlib.suppress(Exception):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard page."""
    try:
        with open("static/dashboard.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content=(
                "<h1>TriggersAPI</h1>"
                "<p>Visit <a href='/docs'>/docs</a> for API documentation.</p>"
            )
        )


@app.get("/explorer", response_class=HTMLResponse)
async def explorer():
    """Serve the explorer page."""
    try:
        with open("static/explorer.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Explorer</h1><p>Page not found.</p>")


@app.get("/api-reference", response_class=HTMLResponse)
async def api_reference():
    """Serve the API reference page."""
    try:
        with open("static/api_reference.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>API Reference</h1><p>Page not found.</p>")


@app.get("/subscriptions-page", response_class=HTMLResponse)
async def subscriptions_page():
    """Serve the subscriptions manager page."""
    try:
        with open("static/subscriptions.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Subscriptions</h1><p>Page not found.</p>")


@app.get("/api/v1/stats")
async def get_stats():
    """Get system-wide statistics."""
    db = get_database()
    return db.get_stats()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "triggers-api", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    from src.config import HOST, PORT

    uvicorn.run("src.main:app", host=HOST, port=PORT, reload=DEBUG)
