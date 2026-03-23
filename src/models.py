from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    ingested = "ingested"
    queued = "queued"
    delivered = "delivered"
    failed = "failed"


class EventCreate(BaseModel):
    event_type: str = Field(..., description="Type of event, e.g. 'order.created'")
    source: str = Field(..., description="Source system identifier")
    payload: dict[str, Any] = Field(..., description="The actual event data")
    timestamp: datetime | None = Field(None, description="Event timestamp (defaults to now)")


class Event(BaseModel):
    id: str
    event_type: str
    source: str
    payload: dict[str, Any]
    status: EventStatus
    timestamp: datetime
    received_at: datetime
    delivered_at: datetime | None = None
    retry_count: int = 0


class EventAck(BaseModel):
    event_ids: list[str] = Field(..., description="List of event IDs to acknowledge")


class SubscriptionCreate(BaseModel):
    name: str = Field(..., description="Subscription name")
    endpoint_url: str = Field(..., description="URL to deliver events to")
    event_types: list[str] | None = Field(None, description="Filter by event types (null = all)")
    sources: list[str] | None = Field(None, description="Filter by sources (null = all)")
    retry_enabled: bool = Field(True, description="Enable exponential backoff retries")
    max_retries: int = Field(5, description="Maximum retry attempts")


class Subscription(BaseModel):
    id: str
    name: str
    endpoint_url: str
    event_types: list[str] | None = None
    sources: list[str] | None = None
    status: str = "active"
    retry_enabled: bool = True
    max_retries: int = 5
    created_at: datetime
    success_count: int = 0
    failure_count: int = 0
    total_delivered: int = 0


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    endpoint_url: str | None = None
    event_types: list[str] | None = None
    sources: list[str] | None = None
    status: str | None = None
    retry_enabled: bool | None = None
    max_retries: int | None = None


class DeliveryAttempt(BaseModel):
    id: str
    event_id: str
    subscription_id: str
    status: str  # pending, success, failed
    attempt_number: int
    response_code: int | None = None
    error_message: str | None = None
    attempted_at: datetime


class StatsResponse(BaseModel):
    total_events: int
    events_by_status: dict[str, int]
    total_subscriptions: int
    active_subscriptions: int
    success_rate: float
    avg_latency_ms: float | None = None
