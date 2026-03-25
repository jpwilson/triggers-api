from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from src.models import (
    DeliveryAttempt,
    Event,
    EventCreate,
    EventStatus,
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
)


def _get_db_path(db_url: str) -> str:
    return db_url.replace("sqlite:///", "")


class Database:
    def __init__(self, db_path: str = "./triggers.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ingested',
                    timestamp TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    delivered_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    request_meta TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
                CREATE INDEX IF NOT EXISTS idx_events_received ON events(received_at);

                CREATE TABLE IF NOT EXISTS subscriptions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    event_types TEXT,
                    sources TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    retry_enabled INTEGER DEFAULT 1,
                    max_retries INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS delivery_attempts (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    subscription_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempt_number INTEGER DEFAULT 1,
                    response_code INTEGER,
                    error_message TEXT,
                    attempted_at TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events(id),
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_delivery_event ON delivery_attempts(event_id);
                CREATE INDEX IF NOT EXISTS idx_delivery_sub ON delivery_attempts(subscription_id);
            """)
            # Migrate: add request_meta column if missing (for existing DBs)
            import contextlib

            with contextlib.suppress(Exception):
                conn.execute("ALTER TABLE events ADD COLUMN request_meta TEXT")
            conn.commit()
        finally:
            conn.close()

    def create_event(self, event_data: EventCreate, request_meta: dict | None = None) -> Event:
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        timestamp = event_data.timestamp or now

        event = Event(
            id=event_id,
            event_type=event_data.event_type,
            source=event_data.source,
            payload=event_data.payload,
            status=EventStatus.ingested,
            timestamp=timestamp,
            received_at=now,
            request_meta=request_meta,
        )

        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO events
                   (id, event_type, source, payload, status, timestamp,
                    received_at, request_meta)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.id,
                    event.event_type,
                    event.source,
                    json.dumps(event.payload),
                    event.status.value,
                    event.timestamp.isoformat(),
                    event.received_at.isoformat(),
                    json.dumps(request_meta) if request_meta else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return event

    def get_inbox(
        self,
        status: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[Event]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM events WHERE 1=1"
            params: list = []

            if status:
                query += " AND status = ?"
                params.append(status)
            else:
                query += " AND status IN ('ingested', 'queued')"

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if source:
                query += " AND source = ?"
                params.append(source)

            if cursor:
                query += " AND received_at < ?"
                params.append(cursor)

            query += " ORDER BY received_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def get_event(self, event_id: str) -> Event | None:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
            return self._row_to_event(row) if row else None
        finally:
            conn.close()

    def get_all_events(
        self,
        limit: int = 50,
        event_type: str | None = None,
        source: str | None = None,
    ) -> list[Event]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM events WHERE 1=1"
            params: list = []
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            if source:
                query += " AND source = ?"
                params.append(source)
            query += " ORDER BY received_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_event(row) for row in rows]
        finally:
            conn.close()

    def acknowledge_events(self, event_ids: list[str]) -> list[str]:
        conn = self._get_conn()
        acknowledged = []
        try:
            now = datetime.now(timezone.utc).isoformat()
            for eid in event_ids:
                result = conn.execute(
                    "UPDATE events SET status = 'delivered', delivered_at = ?"
                    " WHERE id = ? AND status IN ('ingested', 'queued')",
                    (now, eid),
                )
                if result.rowcount > 0:
                    acknowledged.append(eid)
            conn.commit()
        finally:
            conn.close()
        return acknowledged

    def update_event_status(self, event_id: str, status: EventStatus):
        conn = self._get_conn()
        try:
            conn.execute("UPDATE events SET status = ? WHERE id = ?", (status.value, event_id))
            conn.commit()
        finally:
            conn.close()

    def delete_event(self, event_id: str) -> bool:
        conn = self._get_conn()
        try:
            result = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            return result.rowcount > 0
        finally:
            conn.close()

    # --- Subscriptions ---

    def create_subscription(self, sub_data: SubscriptionCreate) -> Subscription:
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        sub = Subscription(
            id=sub_id,
            name=sub_data.name,
            endpoint_url=sub_data.endpoint_url,
            event_types=sub_data.event_types,
            sources=sub_data.sources,
            retry_enabled=sub_data.retry_enabled,
            max_retries=sub_data.max_retries,
            created_at=now,
        )

        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO subscriptions (id, name, endpoint_url,
                   event_types, sources, status, retry_enabled,
                   max_retries, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sub.id,
                    sub.name,
                    sub.endpoint_url,
                    json.dumps(sub.event_types) if sub.event_types else None,
                    json.dumps(sub.sources) if sub.sources else None,
                    sub.status,
                    1 if sub.retry_enabled else 0,
                    sub.max_retries,
                    sub.created_at.isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return sub

    def get_subscription(self, sub_id: str) -> Subscription | None:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,)).fetchone()
            return self._row_to_subscription(row) if row else None
        finally:
            conn.close()

    def list_subscriptions(self, status: str | None = None) -> list[Subscription]:
        conn = self._get_conn()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM subscriptions WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM subscriptions ORDER BY created_at DESC"
                ).fetchall()
            return [self._row_to_subscription(row) for row in rows]
        finally:
            conn.close()

    def update_subscription(self, sub_id: str, update: SubscriptionUpdate) -> Subscription | None:
        conn = self._get_conn()
        try:
            existing = self.get_subscription(sub_id)
            if not existing:
                return None

            updates = []
            params = []
            if update.name is not None:
                updates.append("name = ?")
                params.append(update.name)
            if update.endpoint_url is not None:
                updates.append("endpoint_url = ?")
                params.append(update.endpoint_url)
            if update.event_types is not None:
                updates.append("event_types = ?")
                params.append(json.dumps(update.event_types))
            if update.sources is not None:
                updates.append("sources = ?")
                params.append(json.dumps(update.sources))
            if update.status is not None:
                updates.append("status = ?")
                params.append(update.status)
            if update.retry_enabled is not None:
                updates.append("retry_enabled = ?")
                params.append(1 if update.retry_enabled else 0)
            if update.max_retries is not None:
                updates.append("max_retries = ?")
                params.append(update.max_retries)

            if updates:
                params.append(sub_id)
                conn.execute(
                    f"UPDATE subscriptions SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
                conn.commit()

            return self.get_subscription(sub_id)
        finally:
            conn.close()

    def delete_subscription(self, sub_id: str) -> bool:
        conn = self._get_conn()
        try:
            result = conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
            conn.commit()
            return result.rowcount > 0
        finally:
            conn.close()

    def get_matching_subscriptions(self, event: Event) -> list[Subscription]:
        subs = self.list_subscriptions(status="active")
        matching = []
        for sub in subs:
            if sub.event_types and event.event_type not in sub.event_types:
                continue
            if sub.sources and event.source not in sub.sources:
                continue
            matching.append(sub)
        return matching

    # --- Delivery Attempts ---

    def record_delivery_attempt(
        self,
        event_id: str,
        subscription_id: str,
        status: str,
        attempt_number: int,
        response_code: int | None = None,
        error_message: str | None = None,
    ) -> DeliveryAttempt:
        attempt_id = f"del_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        attempt = DeliveryAttempt(
            id=attempt_id,
            event_id=event_id,
            subscription_id=subscription_id,
            status=status,
            attempt_number=attempt_number,
            response_code=response_code,
            error_message=error_message,
            attempted_at=now,
        )

        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO delivery_attempts (id, event_id,
                   subscription_id, status, attempt_number,
                   response_code, error_message, attempted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    attempt.id,
                    attempt.event_id,
                    attempt.subscription_id,
                    attempt.status,
                    attempt.attempt_number,
                    attempt.response_code,
                    attempt.error_message,
                    attempt.attempted_at.isoformat(),
                ),
            )

            # Update subscription counters
            if status == "success":
                conn.execute(
                    "UPDATE subscriptions SET success_count = success_count + 1,"
                    " total_delivered = total_delivered + 1 WHERE id = ?",
                    (subscription_id,),
                )
            elif status == "failed":
                conn.execute(
                    "UPDATE subscriptions SET failure_count = failure_count + 1 WHERE id = ?",
                    (subscription_id,),
                )

            conn.commit()
        finally:
            conn.close()

        return attempt

    def get_delivery_attempts(
        self, event_id: str | None = None, subscription_id: str | None = None
    ) -> list[DeliveryAttempt]:
        conn = self._get_conn()
        try:
            query = "SELECT * FROM delivery_attempts WHERE 1=1"
            params: list = []
            if event_id:
                query += " AND event_id = ?"
                params.append(event_id)
            if subscription_id:
                query += " AND subscription_id = ?"
                params.append(subscription_id)
            query += " ORDER BY attempted_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_delivery_attempt(row) for row in rows]
        finally:
            conn.close()

    # --- Stats ---

    def get_stats(self) -> dict:
        conn = self._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            status_counts = {}
            for row in conn.execute(
                "SELECT status, COUNT(*) as cnt FROM events GROUP BY status"
            ).fetchall():
                status_counts[row["status"]] = row["cnt"]

            total_subs = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
            active_subs = conn.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
            ).fetchone()[0]

            success = conn.execute(
                "SELECT COUNT(*) FROM delivery_attempts WHERE status = 'success'"
            ).fetchone()[0]
            total_attempts = conn.execute("SELECT COUNT(*) FROM delivery_attempts").fetchone()[0]

            success_rate = (success / total_attempts * 100) if total_attempts > 0 else 100.0

            return {
                "total_events": total,
                "events_by_status": status_counts,
                "total_subscriptions": total_subs,
                "active_subscriptions": active_subs,
                "success_rate": round(success_rate, 2),
            }
        finally:
            conn.close()

    # --- Row converters ---

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        request_meta = None
        try:
            rm = row["request_meta"]
            if rm:
                request_meta = json.loads(rm)
        except (KeyError, IndexError):
            pass
        return Event(
            id=row["id"],
            event_type=row["event_type"],
            source=row["source"],
            payload=json.loads(row["payload"]),
            status=EventStatus(row["status"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            received_at=datetime.fromisoformat(row["received_at"]),
            delivered_at=(
                datetime.fromisoformat(row["delivered_at"]) if row["delivered_at"] else None
            ),
            retry_count=row["retry_count"],
            request_meta=request_meta,
        )

    def _row_to_subscription(self, row: sqlite3.Row) -> Subscription:
        return Subscription(
            id=row["id"],
            name=row["name"],
            endpoint_url=row["endpoint_url"],
            event_types=json.loads(row["event_types"]) if row["event_types"] else None,
            sources=json.loads(row["sources"]) if row["sources"] else None,
            status=row["status"],
            retry_enabled=bool(row["retry_enabled"]),
            max_retries=row["max_retries"],
            created_at=datetime.fromisoformat(row["created_at"]),
            success_count=row["success_count"],
            failure_count=row["failure_count"],
            total_delivered=row["total_delivered"],
        )

    def _row_to_delivery_attempt(self, row: sqlite3.Row) -> DeliveryAttempt:
        return DeliveryAttempt(
            id=row["id"],
            event_id=row["event_id"],
            subscription_id=row["subscription_id"],
            status=row["status"],
            attempt_number=row["attempt_number"],
            response_code=row["response_code"],
            error_message=row["error_message"],
            attempted_at=datetime.fromisoformat(row["attempted_at"]),
        )
