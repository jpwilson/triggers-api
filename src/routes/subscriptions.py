from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.database import Database
from src.models import DeliveryAttempt, Subscription, SubscriptionCreate, SubscriptionUpdate

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_db() -> Database:
    from src.main import get_database

    return get_database()


@router.post("", response_model=Subscription, status_code=201)
async def create_subscription(sub_data: SubscriptionCreate):
    """Create a new subscription for push delivery.

    Events matching the configured filters (event_types, sources) will be
    delivered to the specified endpoint URL with optional retry logic.
    """
    db = get_db()
    return db.create_subscription(sub_data)


@router.get("", response_model=list[Subscription])
async def list_subscriptions(status: str | None = None):
    """List all subscriptions, optionally filtered by status."""
    db = get_db()
    return db.list_subscriptions(status=status)


@router.get("/{sub_id}", response_model=Subscription)
async def get_subscription(sub_id: str):
    """Get a specific subscription by ID."""
    db = get_db()
    sub = db.get_subscription(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
    return sub


@router.patch("/{sub_id}", response_model=Subscription)
async def update_subscription(sub_id: str, update: SubscriptionUpdate):
    """Update a subscription's configuration."""
    db = get_db()
    sub = db.update_subscription(sub_id, update)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
    return sub


@router.delete("/{sub_id}", status_code=204)
async def delete_subscription(sub_id: str):
    """Delete a subscription."""
    db = get_db()
    if not db.delete_subscription(sub_id):
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")


@router.get("/{sub_id}/deliveries", response_model=list[DeliveryAttempt])
async def get_subscription_deliveries(sub_id: str):
    """Get delivery attempts for a specific subscription."""
    db = get_db()
    sub = db.get_subscription(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Subscription {sub_id} not found")
    return db.get_delivery_attempts(subscription_id=sub_id)
