from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from src.database import Database
from src.models import EventAck

router = APIRouter(prefix="/inbox", tags=["Inbox"])


def get_db() -> Database:
    from src.main import get_database

    return get_database()


@router.get("", response_model=dict[str, Any])
async def get_inbox(
    event_type: str | None = Query(None, description="Filter by event type"),
    source: str | None = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    cursor: str | None = Query(None, description="Cursor for pagination (received_at timestamp)"),
):
    """Retrieve undelivered events from the inbox.

    Returns events with status 'ingested' or 'queued' that haven't been
    acknowledged yet. Supports cursor-based pagination.
    """
    db = get_db()
    events = db.get_inbox(
        event_type=event_type,
        source=source,
        limit=limit,
        cursor=cursor,
    )

    next_cursor = None
    if events and len(events) == limit:
        next_cursor = events[-1].received_at.isoformat()

    return {
        "events": events,
        "count": len(events),
        "next_cursor": next_cursor,
    }


@router.post("/ack", response_model=dict[str, Any])
async def acknowledge_events(ack_data: EventAck):
    """Acknowledge receipt of events, marking them as delivered.

    Once acknowledged, events are removed from the inbox and won't be
    returned by subsequent GET /inbox calls.
    """
    db = get_db()
    acknowledged = db.acknowledge_events(ack_data.event_ids)

    return {
        "acknowledged": acknowledged,
        "count": len(acknowledged),
        "message": f"Successfully acknowledged {len(acknowledged)} event(s)",
    }
