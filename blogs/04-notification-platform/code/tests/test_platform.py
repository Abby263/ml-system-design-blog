import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.models import Channel, DeliveryState, NotificationRequest, Priority
from app.providers import ProviderFactory
from app.service import NotificationService
from app.state import full_jitter_delay, should_apply_callback
from app.store import IdempotencyConflict, Store
from app.worker import Worker


class StateTests(unittest.TestCase):
    def test_full_jitter_is_bounded(self) -> None:
        self.assertEqual(full_jitter_delay(3, 1.0, 60.0, random_value=0.5), 2.0)
        self.assertEqual(full_jitter_delay(20, 1.0, 60.0, random_value=1.0), 60.0)

    def test_callback_cannot_move_delivered_backward(self) -> None:
        self.assertFalse(should_apply_callback(DeliveryState.DELIVERED, DeliveryState.FAILED))
        self.assertTrue(should_apply_callback(DeliveryState.DELIVERED, DeliveryState.READ))


class PlatformTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = str(Path(self.temp_dir.name) / "notifications.db")
        self.store = Store(self.database_path)
        self.store.initialize()
        self.service = NotificationService(self.store)
        self.now = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def request(self, recipient_id: str = "user-1") -> NotificationRequest:
        return NotificationRequest(
            recipient_id=recipient_id,
            template="order-receipt",
            channels=[Channel.EMAIL, Channel.PUSH],
            data={"order_id": "742"},
            priority=Priority.TRANSACTIONAL,
            expires_at=self.now + timedelta(minutes=10),
        )

    def submit(self, key: str = "receipt-742", recipient_id: str = "user-1"):
        return self.service.submit(
            tenant_id="demo",
            idempotency_key=key,
            request=self.request(recipient_id),
            now=self.now,
        )

    def worker(self) -> Worker:
        return Worker(
            self.store,
            ProviderFactory(),
            lease_seconds=30,
            max_attempts=3,
            retry_base_seconds=1.0,
            retry_max_seconds=10.0,
            random_value=0.5,
        )

    def test_submission_is_idempotent(self) -> None:
        first = self.submit()
        second = self.submit()
        self.assertEqual(first.notification_id, second.notification_id)
        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)

    def test_idempotency_key_rejects_different_input(self) -> None:
        self.submit()
        with self.assertRaises(IdempotencyConflict):
            self.submit(recipient_id="different-user")

    def test_fanout_and_provider_acceptance(self) -> None:
        accepted = self.submit()
        worker = self.worker()
        current = self.now.timestamp()
        self.assertTrue(worker.process_one(current))
        self.assertTrue(worker.process_one(current))
        self.assertTrue(worker.process_one(current))
        _, deliveries = self.store.notification(accepted.notification_id)
        self.assertEqual(len(deliveries), 2)
        self.assertEqual(
            {row["state"] for row in deliveries}, {DeliveryState.PROVIDER_ACCEPTED.value}
        )

    def test_retryable_result_is_scheduled_then_accepted(self) -> None:
        accepted = self.service.submit(
            tenant_id="demo",
            idempotency_key="retry-once",
            request=NotificationRequest(
                recipient_id="retry-user",
                template="security-alert",
                channels=[Channel.SMS],
                expires_at=self.now + timedelta(minutes=10),
            ),
            now=self.now,
        )
        worker = self.worker()
        current = self.now.timestamp()
        worker.process_one(current)
        worker.process_one(current)
        _, deliveries = self.store.notification(accepted.notification_id)
        self.assertEqual(deliveries[0]["state"], DeliveryState.RETRY_SCHEDULED.value)
        worker.process_one(current + 2.0)
        _, deliveries = self.store.notification(accepted.notification_id)
        self.assertEqual(deliveries[0]["state"], DeliveryState.PROVIDER_ACCEPTED.value)
        self.assertEqual(deliveries[0]["attempts"], 2)

    def test_invalid_endpoint_fails_without_retry(self) -> None:
        accepted = self.service.submit(
            tenant_id="demo",
            idempotency_key="invalid",
            request=NotificationRequest(
                recipient_id="invalid-user",
                template="security-alert",
                channels=[Channel.PUSH],
                expires_at=self.now + timedelta(minutes=10),
            ),
            now=self.now,
        )
        worker = self.worker()
        current = self.now.timestamp()
        worker.process_one(current)
        worker.process_one(current)
        _, deliveries = self.store.notification(accepted.notification_id)
        self.assertEqual(deliveries[0]["state"], DeliveryState.FAILED.value)
        self.assertEqual(deliveries[0]["attempts"], 1)

    def test_callback_is_deduplicated_and_monotonic(self) -> None:
        accepted = self.submit()
        worker = self.worker()
        current = self.now.timestamp()
        worker.process_one(current)
        worker.process_one(current)
        _, deliveries = self.store.notification(accepted.notification_id)
        delivery_id = deliveries[0]["id"]
        self.assertTrue(
            self.store.apply_provider_event(
                provider="fake-email",
                event_id="evt-1",
                delivery_id=delivery_id,
                incoming=DeliveryState.DELIVERED,
                raw_json="{}",
                now=current + 5,
            )
        )
        self.assertFalse(
            self.store.apply_provider_event(
                provider="fake-email",
                event_id="evt-1",
                delivery_id=delivery_id,
                incoming=DeliveryState.DELIVERED,
                raw_json="{}",
                now=current + 6,
            )
        )
        self.store.apply_provider_event(
            provider="fake-email",
            event_id="evt-2",
            delivery_id=delivery_id,
            incoming=DeliveryState.FAILED,
            raw_json="{}",
            now=current + 7,
        )
        self.assertEqual(self.store.delivery(delivery_id)["state"], DeliveryState.DELIVERED.value)


if __name__ == "__main__":
    unittest.main()
