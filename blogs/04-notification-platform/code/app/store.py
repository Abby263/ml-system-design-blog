import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .models import DeliveryState, Priority
from .state import should_apply_callback


SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    template TEXT NOT NULL,
    channels_json TEXT NOT NULL,
    data_json TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS deliveries (
    id TEXT PRIMARY KEY,
    notification_id TEXT NOT NULL REFERENCES notifications(id),
    channel TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL,
    provider TEXT,
    provider_message_id TEXT,
    last_error TEXT,
    version INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    UNIQUE (notification_id, channel, endpoint)
);

CREATE TABLE IF NOT EXISTS outbox_jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    priority INTEGER NOT NULL,
    available_at REAL NOT NULL,
    lease_until REAL,
    completed_at REAL,
    UNIQUE (kind, aggregate_id)
);

CREATE TABLE IF NOT EXISTS provider_events (
    provider TEXT NOT NULL,
    event_id TEXT NOT NULL,
    delivery_id TEXT NOT NULL REFERENCES deliveries(id),
    status TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (provider, event_id)
);

CREATE INDEX IF NOT EXISTS idx_outbox_available
ON outbox_jobs (completed_at, available_at, priority);
"""


class IdempotencyConflict(Exception):
    pass


@dataclass(frozen=True)
class SubmissionRecord:
    notification_id: str
    duplicate: bool


@dataclass(frozen=True)
class Job:
    id: str
    kind: str
    aggregate_id: str


class Store:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_notification(
        self,
        *,
        notification_id: str,
        tenant_id: str,
        idempotency_key: str,
        request_hash: str,
        recipient_id: str,
        template: str,
        channels_json: str,
        data_json: str,
        priority: Priority,
        created_at: float,
        expires_at: float,
    ) -> SubmissionRecord:
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT id, request_hash FROM notifications "
                "WHERE tenant_id = ? AND idempotency_key = ?",
                (tenant_id, idempotency_key),
            ).fetchone()
            if existing:
                if existing["request_hash"] != request_hash:
                    raise IdempotencyConflict("idempotency key was used with different input")
                return SubmissionRecord(existing["id"], duplicate=True)

            connection.execute(
                """
                INSERT INTO notifications (
                    id, tenant_id, idempotency_key, request_hash, recipient_id,
                    template, channels_json, data_json, priority, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_id,
                    tenant_id,
                    idempotency_key,
                    request_hash,
                    recipient_id,
                    template,
                    channels_json,
                    data_json,
                    priority.value,
                    created_at,
                    expires_at,
                ),
            )
            connection.execute(
                "INSERT INTO outbox_jobs (id, kind, aggregate_id, priority, available_at) "
                "VALUES (?, 'fanout', ?, ?, ?)",
                (
                    f"job_fanout_{notification_id}",
                    notification_id,
                    priority_rank(priority),
                    created_at,
                ),
            )
            return SubmissionRecord(notification_id, duplicate=False)

    def claim_job(self, now: float, lease_seconds: int) -> Job | None:
        with self.transaction() as connection:
            row = connection.execute(
                """
                SELECT id, kind, aggregate_id
                FROM outbox_jobs
                WHERE completed_at IS NULL
                  AND available_at <= ?
                  AND (lease_until IS NULL OR lease_until <= ?)
                ORDER BY priority ASC, available_at ASC
                LIMIT 1
                """,
                (now, now),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE outbox_jobs SET lease_until = ? WHERE id = ?",
                (now + lease_seconds, row["id"]),
            )
            return Job(row["id"], row["kind"], row["aggregate_id"])

    def fanout(self, job: Job, now: float) -> int:
        with self.transaction() as connection:
            notification = connection.execute(
                "SELECT * FROM notifications WHERE id = ?", (job.aggregate_id,)
            ).fetchone()
            if notification is None:
                raise KeyError(job.aggregate_id)
            channels = json.loads(notification["channels_json"])
            created = 0
            for channel in channels:
                endpoint = f"{channel}:{notification['recipient_id']}"
                delivery_id = stable_delivery_id(notification["id"], channel, endpoint)
                result = connection.execute(
                    """
                    INSERT OR IGNORE INTO deliveries (
                        id, notification_id, channel, endpoint, state, next_attempt_at,
                        created_at, updated_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        delivery_id,
                        notification["id"],
                        channel,
                        endpoint,
                        DeliveryState.QUEUED.value,
                        now,
                        now,
                        now,
                        notification["expires_at"],
                    ),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO outbox_jobs
                        (id, kind, aggregate_id, priority, available_at)
                    VALUES (?, 'send', ?, ?, ?)
                    """,
                    (
                        f"job_send_{delivery_id}",
                        delivery_id,
                        priority_rank(Priority(notification["priority"])),
                        now,
                    ),
                )
                created += result.rowcount
            connection.execute(
                "UPDATE outbox_jobs SET completed_at = ?, lease_until = NULL WHERE id = ?",
                (now, job.id),
            )
            return created

    def start_attempt(self, job: Job, now: float) -> sqlite3.Row | None:
        with self.transaction() as connection:
            delivery = connection.execute(
                """
                SELECT d.*, n.template, n.data_json
                FROM deliveries d JOIN notifications n ON n.id = d.notification_id
                WHERE d.id = ?
                """,
                (job.aggregate_id,),
            ).fetchone()
            if delivery is None:
                raise KeyError(job.aggregate_id)
            if DeliveryState(delivery["state"]) in {
                DeliveryState.PROVIDER_ACCEPTED,
                DeliveryState.DELIVERED,
                DeliveryState.READ,
                DeliveryState.SUPPRESSED,
                DeliveryState.EXPIRED,
                DeliveryState.FAILED,
            }:
                connection.execute(
                    "UPDATE outbox_jobs SET completed_at = ?, lease_until = NULL WHERE id = ?",
                    (now, job.id),
                )
                return None
            if now >= delivery["expires_at"]:
                connection.execute(
                    "UPDATE deliveries SET state = ?, updated_at = ?, version = version + 1 "
                    "WHERE id = ?",
                    (DeliveryState.EXPIRED.value, now, delivery["id"]),
                )
                connection.execute(
                    "UPDATE outbox_jobs SET completed_at = ?, lease_until = NULL WHERE id = ?",
                    (now, job.id),
                )
                return None
            connection.execute(
                """
                UPDATE deliveries
                SET state = ?, attempts = attempts + 1, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (DeliveryState.SENDING.value, now, delivery["id"]),
            )
            return connection.execute(
                """
                SELECT d.*, n.template, n.data_json
                FROM deliveries d JOIN notifications n ON n.id = d.notification_id
                WHERE d.id = ?
                """,
                (delivery["id"],),
            ).fetchone()

    def mark_accepted(self, job: Job, provider: str, provider_message_id: str, now: float) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                UPDATE deliveries
                SET state = ?, provider = ?, provider_message_id = ?, last_error = NULL,
                    updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (
                    DeliveryState.PROVIDER_ACCEPTED.value,
                    provider,
                    provider_message_id,
                    now,
                    job.aggregate_id,
                ),
            )
            connection.execute(
                "UPDATE outbox_jobs SET completed_at = ?, lease_until = NULL WHERE id = ?",
                (now, job.id),
            )

    def schedule_retry(self, job: Job, error: str, available_at: float, now: float) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                UPDATE deliveries
                SET state = ?, last_error = ?, next_attempt_at = ?, updated_at = ?,
                    version = version + 1
                WHERE id = ?
                """,
                (
                    DeliveryState.RETRY_SCHEDULED.value,
                    error,
                    available_at,
                    now,
                    job.aggregate_id,
                ),
            )
            connection.execute(
                "UPDATE outbox_jobs SET available_at = ?, lease_until = NULL WHERE id = ?",
                (available_at, job.id),
            )

    def mark_failed(self, job: Job, error: str, now: float) -> None:
        with self.transaction() as connection:
            connection.execute(
                """
                UPDATE deliveries
                SET state = ?, last_error = ?, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (DeliveryState.FAILED.value, error, now, job.aggregate_id),
            )
            connection.execute(
                "UPDATE outbox_jobs SET completed_at = ?, lease_until = NULL WHERE id = ?",
                (now, job.id),
            )

    def apply_provider_event(
        self,
        *,
        provider: str,
        event_id: str,
        delivery_id: str,
        incoming: DeliveryState,
        raw_json: str,
        now: float,
    ) -> bool:
        with self.transaction() as connection:
            delivery = connection.execute(
                "SELECT state FROM deliveries WHERE id = ?", (delivery_id,)
            ).fetchone()
            if delivery is None:
                raise KeyError(delivery_id)
            inserted = connection.execute(
                """
                INSERT OR IGNORE INTO provider_events
                    (provider, event_id, delivery_id, status, raw_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider, event_id, delivery_id, incoming.value, raw_json, now),
            )
            if inserted.rowcount == 0:
                return False
            current = DeliveryState(delivery["state"])
            if should_apply_callback(current, incoming):
                connection.execute(
                    "UPDATE deliveries SET state = ?, updated_at = ?, version = version + 1 "
                    "WHERE id = ?",
                    (incoming.value, now, delivery_id),
                )
            return True

    def notification(self, notification_id: str) -> tuple[sqlite3.Row, list[sqlite3.Row]] | None:
        with self.connect() as connection:
            notification = connection.execute(
                "SELECT * FROM notifications WHERE id = ?", (notification_id,)
            ).fetchone()
            if notification is None:
                return None
            deliveries = connection.execute(
                "SELECT * FROM deliveries WHERE notification_id = ? ORDER BY channel",
                (notification_id,),
            ).fetchall()
            return notification, deliveries

    def delivery(self, delivery_id: str) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM deliveries WHERE id = ?", (delivery_id,)
            ).fetchone()


def priority_rank(priority: Priority) -> int:
    return {Priority.TRANSACTIONAL: 0, Priority.NORMAL: 1, Priority.BULK: 2}[priority]


def stable_delivery_id(notification_id: str, channel: str, endpoint: str) -> str:
    from hashlib import sha256

    digest = sha256(f"{notification_id}:{channel}:{endpoint}".encode()).hexdigest()[:24]
    return f"dlv_{digest}"


def timestamp(value: datetime) -> float:
    return value.timestamp()
