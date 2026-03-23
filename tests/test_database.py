import os
import tempfile

from src.database import Database
from src.models import EventCreate, EventStatus, SubscriptionCreate


def make_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_name = tmp.name
    return Database(db_path=tmp_name), tmp_name


def test_create_event():
    db, path = make_db()
    try:
        event = db.create_event(
            EventCreate(
                event_type="test.event",
                source="unit_test",
                payload={"key": "value"},
            )
        )
        assert event.id.startswith("evt_")
        assert event.status == EventStatus.ingested
        assert event.payload == {"key": "value"}
    finally:
        os.unlink(path)


def test_get_event():
    db, path = make_db()
    try:
        created = db.create_event(
            EventCreate(
                event_type="test.event",
                source="unit_test",
                payload={"key": "value"},
            )
        )
        fetched = db.get_event(created.id)
        assert fetched is not None
        assert fetched.id == created.id
    finally:
        os.unlink(path)


def test_get_event_not_found():
    db, path = make_db()
    try:
        assert db.get_event("evt_nonexistent") is None
    finally:
        os.unlink(path)


def test_acknowledge_events():
    db, path = make_db()
    try:
        e1 = db.create_event(EventCreate(event_type="t", source="s", payload={}))
        e2 = db.create_event(EventCreate(event_type="t", source="s", payload={}))
        acked = db.acknowledge_events([e1.id, e2.id])
        assert len(acked) == 2

        # Check they're now delivered
        updated = db.get_event(e1.id)
        assert updated.status == EventStatus.delivered
    finally:
        os.unlink(path)


def test_create_subscription():
    db, path = make_db()
    try:
        sub = db.create_subscription(
            SubscriptionCreate(
                name="Test",
                endpoint_url="https://example.com",
                event_types=["order.created"],
            )
        )
        assert sub.id.startswith("sub_")
        assert sub.status == "active"
    finally:
        os.unlink(path)


def test_matching_subscriptions():
    db, path = make_db()
    try:
        db.create_subscription(
            SubscriptionCreate(
                name="Order Sub",
                endpoint_url="https://example.com",
                event_types=["order.created"],
                sources=["shopify"],
            )
        )
        db.create_subscription(
            SubscriptionCreate(
                name="All Events",
                endpoint_url="https://example.com/all",
            )
        )

        event = db.create_event(
            EventCreate(
                event_type="order.created",
                source="shopify",
                payload={},
            )
        )

        matching = db.get_matching_subscriptions(event)
        assert len(matching) == 2

        # Non-matching event
        event2 = db.create_event(
            EventCreate(
                event_type="payment.failed",
                source="stripe",
                payload={},
            )
        )
        matching2 = db.get_matching_subscriptions(event2)
        assert len(matching2) == 1  # Only the "All Events" sub
    finally:
        os.unlink(path)


def test_get_stats():
    db, path = make_db()
    try:
        stats = db.get_stats()
        assert stats["total_events"] == 0
        assert stats["total_subscriptions"] == 0

        db.create_event(EventCreate(event_type="t", source="s", payload={}))
        db.create_subscription(SubscriptionCreate(name="S", endpoint_url="https://example.com"))

        stats = db.get_stats()
        assert stats["total_events"] == 1
        assert stats["total_subscriptions"] == 1
    finally:
        os.unlink(path)
