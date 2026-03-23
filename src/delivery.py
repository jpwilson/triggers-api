import asyncio
import logging

import httpx

from src.database import Database
from src.models import Event, EventStatus, Subscription

logger = logging.getLogger(__name__)

# Exponential backoff delays in seconds: 1s, 2s, 4s, 8s, 16s
BACKOFF_DELAYS = [1, 2, 4, 8, 16]


async def deliver_event(db: Database, event: Event, subscription: Subscription) -> bool:
    """Deliver an event to a subscription endpoint with retry logic."""
    max_attempts = subscription.max_retries if subscription.retry_enabled else 1

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    subscription.endpoint_url,
                    json={
                        "event_id": event.id,
                        "event_type": event.event_type,
                        "source": event.source,
                        "payload": event.payload,
                        "timestamp": event.timestamp.isoformat(),
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-TriggersAPI-Event-ID": event.id,
                        "X-TriggersAPI-Subscription-ID": subscription.id,
                        "X-TriggersAPI-Attempt": str(attempt),
                    },
                )

                if response.status_code < 400:
                    db.record_delivery_attempt(
                        event_id=event.id,
                        subscription_id=subscription.id,
                        status="success",
                        attempt_number=attempt,
                        response_code=response.status_code,
                    )
                    logger.info(
                        f"Delivered event {event.id} to {subscription.name} "
                        f"(attempt {attempt}, status {response.status_code})"
                    )
                    return True

                db.record_delivery_attempt(
                    event_id=event.id,
                    subscription_id=subscription.id,
                    status="failed",
                    attempt_number=attempt,
                    response_code=response.status_code,
                    error_message=f"HTTP {response.status_code}",
                )
                logger.warning(
                    f"Delivery failed for {event.id} to {subscription.name}: "
                    f"HTTP {response.status_code} (attempt {attempt}/{max_attempts})"
                )

        except Exception as e:
            db.record_delivery_attempt(
                event_id=event.id,
                subscription_id=subscription.id,
                status="failed",
                attempt_number=attempt,
                error_message=str(e),
            )
            logger.warning(
                f"Delivery error for {event.id} to {subscription.name}: "
                f"{e} (attempt {attempt}/{max_attempts})"
            )

        # Backoff before retry
        if attempt < max_attempts and subscription.retry_enabled:
            delay = BACKOFF_DELAYS[min(attempt - 1, len(BACKOFF_DELAYS) - 1)]
            await asyncio.sleep(delay)

    return False


async def process_event_delivery(db: Database, event: Event):
    """Find matching subscriptions and deliver an event to all of them."""
    subscriptions = db.get_matching_subscriptions(event)

    if not subscriptions:
        return

    db.update_event_status(event.id, EventStatus.queued)

    results = await asyncio.gather(
        *[deliver_event(db, event, sub) for sub in subscriptions],
        return_exceptions=True,
    )

    all_success = all(r is True for r in results)
    if all_success or any(r is True for r in results):
        db.update_event_status(event.id, EventStatus.delivered)
    else:
        db.update_event_status(event.id, EventStatus.failed)
