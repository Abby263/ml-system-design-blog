import json
import math
import sqlite3
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from .models import LabelRequest, LabelView, RiskDecisionView, RiskRequest


class IdempotencyConflict(Exception):
    pass


class DecisionNotFound(Exception):
    pass


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    request_hash TEXT NOT NULL,
                    transaction_id TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    card_token TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    country TEXT NOT NULL,
                    amount_minor INTEGER NOT NULL,
                    decision_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS decisions_card_time
                    ON decisions(card_token, event_time);
                CREATE INDEX IF NOT EXISTS decisions_device_time
                    ON decisions(device_id, event_time);
                CREATE TABLE IF NOT EXISTS labels (
                    label_id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL REFERENCES decisions(decision_id),
                    label_type TEXT NOT NULL,
                    label_value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    observed_at TEXT NOT NULL,
                    correction_of TEXT REFERENCES labels(label_id),
                    created_at TEXT NOT NULL
                );
                """
            )

    def _features(self, connection: sqlite3.Connection, request: RiskRequest) -> dict[str, float]:
        event_time = request.event_time.astimezone(UTC)
        ten_minutes_ago = (event_time - timedelta(minutes=10)).isoformat()
        one_hour_ago = (event_time - timedelta(hours=1)).isoformat()
        one_day_ago = (event_time - timedelta(days=1)).isoformat()
        current = event_time.isoformat()
        card_attempts = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM decisions
            WHERE card_token = ? AND event_time >= ? AND event_time <= ?
            """,
            (request.card_token, ten_minutes_ago, current),
        ).fetchone()["count"]
        card_amount = connection.execute(
            """
            SELECT COALESCE(SUM(amount_minor), 0) AS amount
            FROM decisions
            WHERE card_token = ? AND event_time >= ? AND event_time <= ?
            """,
            (request.card_token, one_hour_ago, current),
        ).fetchone()["amount"]
        device_accounts = connection.execute(
            """
            SELECT COUNT(DISTINCT account_id) AS count
            FROM decisions
            WHERE device_id = ? AND event_time >= ? AND event_time <= ?
            """,
            (request.device_id, one_day_ago, current),
        ).fetchone()["count"]
        prior_country = connection.execute(
            """
            SELECT country FROM decisions
            WHERE card_token = ? AND event_time >= ? AND event_time <= ?
            ORDER BY event_time DESC LIMIT 1
            """,
            (request.card_token, one_hour_ago, current),
        ).fetchone()
        account_age_hours = max(
            0.0,
            (event_time - request.account_created_at.astimezone(UTC)).total_seconds() / 3_600,
        )
        return {
            "amount_log": math.log1p(request.amount_minor / 100.0),
            "account_age_hours_log": math.log1p(account_age_hours),
            "card_attempt_count_10m": float(card_attempts + 1),
            "card_amount_1h_log": math.log1p((card_amount + request.amount_minor) / 100.0),
            "device_accounts_24h": float(device_accounts + 1),
            "country_changed_1h": float(
                prior_country is not None and prior_country["country"] != request.country.upper()
            ),
            "cvv_failed": float(request.cvv_result == "fail"),
        }

    def decide(
        self,
        idempotency_key: str,
        request_hash: str,
        request: RiskRequest,
        build: Callable[[dict[str, float]], RiskDecisionView],
    ) -> RiskDecisionView:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT request_hash, decision_json FROM decisions WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                if existing["request_hash"] != request_hash:
                    raise IdempotencyConflict(idempotency_key)
                payload = json.loads(existing["decision_json"])
                payload["idempotent_replay"] = True
                connection.commit()
                return RiskDecisionView.model_validate(payload)

            features = self._features(connection, request)
            decision = build(features)
            payload = decision.model_dump(mode="json")
            connection.execute(
                """
                INSERT INTO decisions (
                    decision_id, idempotency_key, request_hash, transaction_id, event_time,
                    account_id, card_token, device_id, country, amount_minor,
                    decision_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.decision_id,
                    idempotency_key,
                    request_hash,
                    request.transaction_id,
                    request.event_time.astimezone(UTC).isoformat(),
                    request.account_id,
                    request.card_token,
                    request.device_id,
                    request.country.upper(),
                    request.amount_minor,
                    json.dumps(payload, sort_keys=True),
                    datetime.now(UTC).isoformat(),
                ),
            )
            connection.commit()
            return decision
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def add_label(self, decision_id: str, label: LabelRequest) -> LabelView:
        label_id = f"lbl_{uuid.uuid4().hex}"
        with self._connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone():
                raise DecisionNotFound(decision_id)
            if (
                label.correction_of
                and not connection.execute(
                    "SELECT 1 FROM labels WHERE label_id = ? AND decision_id = ?",
                    (label.correction_of, decision_id),
                ).fetchone()
            ):
                raise DecisionNotFound(label.correction_of)
            connection.execute(
                """
                INSERT INTO labels (
                    label_id, decision_id, label_type, label_value, source,
                    confidence, observed_at, correction_of, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    label_id,
                    decision_id,
                    label.label_type,
                    label.label_value,
                    label.source,
                    label.confidence,
                    label.observed_at.astimezone(UTC).isoformat(),
                    label.correction_of,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return LabelView(label_id=label_id, decision_id=decision_id, **label.model_dump())

    def decision_count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0])
