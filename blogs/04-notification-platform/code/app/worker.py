import argparse
import json
import time

from .models import Channel
from .providers import ProviderFactory, ProviderOutcome, ProviderRequest
from .settings import settings
from .state import full_jitter_delay
from .store import Store


class Worker:
    def __init__(
        self,
        store: Store,
        providers: ProviderFactory,
        *,
        lease_seconds: int = 30,
        max_attempts: int = 5,
        retry_base_seconds: float = 1.0,
        retry_max_seconds: float = 60.0,
        random_value: float | None = None,
    ):
        self.store = store
        self.providers = providers
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        self.retry_base_seconds = retry_base_seconds
        self.retry_max_seconds = retry_max_seconds
        self.random_value = random_value

    def process_one(self, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        job = self.store.claim_job(current, self.lease_seconds)
        if job is None:
            return False
        if job.kind == "fanout":
            self.store.fanout(job, current)
            return True
        if job.kind != "send":
            self.store.mark_failed(job, f"unknown job kind: {job.kind}", current)
            return True

        delivery = self.store.start_attempt(job, current)
        if delivery is None:
            return True
        attempt = int(delivery["attempts"])
        request = ProviderRequest(
            delivery_id=delivery["id"],
            channel=Channel(delivery["channel"]),
            endpoint=delivery["endpoint"],
            template=delivery["template"],
            data=json.loads(delivery["data_json"]),
            attempt=attempt,
        )
        adapter = self.providers.for_channel(request.channel)
        result = adapter.send(request)

        if result.outcome == ProviderOutcome.ACCEPTED:
            assert result.provider_message_id is not None
            self.store.mark_accepted(job, result.provider, result.provider_message_id, current)
            return True

        error = result.error or "provider request failed"
        if result.outcome == ProviderOutcome.RETRYABLE and attempt < self.max_attempts:
            delay = full_jitter_delay(
                attempt,
                self.retry_base_seconds,
                self.retry_max_seconds,
                self.random_value,
            )
            delay = max(delay, result.retry_after_seconds or 0.0)
            retry_at = current + delay
            if retry_at < float(delivery["expires_at"]):
                self.store.schedule_retry(job, error, retry_at, current)
                return True

        self.store.mark_failed(job, error, current)
        return True


def build_worker(database_path: str | None = None) -> Worker:
    store = Store(database_path or settings.database_path)
    store.initialize()
    return Worker(
        store,
        ProviderFactory(),
        lease_seconds=settings.job_lease_seconds,
        max_attempts=settings.max_attempts,
        retry_base_seconds=settings.retry_base_seconds,
        retry_max_seconds=settings.retry_max_seconds,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Process durable notification jobs")
    parser.add_argument("--once", action="store_true", help="process at most one available job")
    arguments = parser.parse_args()
    worker = build_worker()
    if arguments.once:
        worker.process_one()
        return
    while True:
        if not worker.process_one():
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
