import unittest
from unittest.mock import patch

from app.identity import partition_key
from app.model import TokenBucketModel
from app.models import RateLimitDecision, RateLimitPolicy


class PolicyTests(unittest.TestCase):
    def test_rejects_invalid_policy(self) -> None:
        with self.assertRaises(ValueError):
            RateLimitPolicy("bad", capacity=0, refill_per_second=1)
        with self.assertRaises(ValueError):
            RateLimitPolicy("bad", capacity=1, refill_per_second=0)
        with self.assertRaises(ValueError):
            RateLimitPolicy("bad", capacity=1, refill_per_second=1, cost=2)

    def test_window_rounds_up(self) -> None:
        policy = RateLimitPolicy("api", capacity=10, refill_per_second=3)
        self.assertEqual(policy.window_seconds, 4)


class TokenBucketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = RateLimitPolicy("test", capacity=3, refill_per_second=1)
        self.bucket = TokenBucketModel(self.policy)

    def test_allows_initial_burst_then_denies(self) -> None:
        self.assertTrue(self.bucket.allow(0).allowed)
        self.assertTrue(self.bucket.allow(0).allowed)
        self.assertTrue(self.bucket.allow(0).allowed)
        denied = self.bucket.allow(0)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.retry_after_ms, 1000)

    def test_refills_with_elapsed_time(self) -> None:
        for _ in range(3):
            self.bucket.allow(0)
        decision = self.bucket.allow(1500)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 0)

    def test_clock_moving_back_does_not_create_tokens(self) -> None:
        for _ in range(3):
            self.bucket.allow(1000)
        self.assertFalse(self.bucket.allow(500).allowed)


class HeaderTests(unittest.TestCase):
    def test_denial_includes_retry_after(self) -> None:
        policy = RateLimitPolicy("writes", capacity=10, refill_per_second=2)
        decision = RateLimitDecision(False, 0, 501, 5000, policy)
        self.assertEqual(decision.headers()["Retry-After"], "1")
        self.assertEqual(decision.headers()["RateLimit"], '"writes";r=0;t=5')

    def test_allowed_response_omits_retry_after(self) -> None:
        policy = RateLimitPolicy("reads", capacity=10, refill_per_second=2)
        decision = RateLimitDecision(True, 7, 0, 1500, policy)
        self.assertNotIn("Retry-After", decision.headers())


class IdentityTests(unittest.TestCase):
    @patch("app.identity.settings")
    def test_partition_key_is_stable_and_hides_identity(self, mock_settings) -> None:
        mock_settings.identity_secret = "test-secret"
        first = partition_key("reads", "api-key:customer-secret")
        second = partition_key("reads", "api-key:customer-secret")
        self.assertEqual(first, second)
        self.assertNotIn("customer-secret", first)
        self.assertRegex(first, r"^rate-limit:v1:reads:\{[0-9a-f]{24}\}$")


if __name__ == "__main__":
    unittest.main()
