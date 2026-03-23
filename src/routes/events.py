from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from src.database import Database
from src.delivery import process_event_delivery
from src.models import Event, EventCreate

router = APIRouter(prefix="/events", tags=["Events"])


def get_db() -> Database:
    from src.main import get_database

    return get_database()


@router.post("", response_model=dict[str, Any], status_code=201)
async def ingest_event(event_data: EventCreate, background_tasks: BackgroundTasks):
    """Ingest a new event into the TriggersAPI.

    Accepts a JSON payload with event details, stores it with metadata,
    and returns a structured acknowledgment.
    """
    db = get_db()
    event = db.create_event(event_data)

    # Trigger async delivery to matching subscriptions
    background_tasks.add_task(process_event_delivery, db, event)

    return {
        "status": "accepted",
        "event_id": event.id,
        "received_at": event.received_at.isoformat(),
        "message": "Event ingested successfully",
    }


@router.get("", response_model=list[Event])
async def list_events(
    event_type: str | None = Query(None, description="Filter by event type"),
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
):
    """List all events with optional filtering."""
    db = get_db()
    return db.get_all_events(limit=limit, event_type=event_type, source=source)


@router.get("/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get a specific event by ID."""
    db = get_db()
    event = db.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str):
    """Delete a specific event."""
    db = get_db()
    if not db.delete_event(event_id):
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
