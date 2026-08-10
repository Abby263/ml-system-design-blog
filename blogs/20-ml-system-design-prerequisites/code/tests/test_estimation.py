import pathlib
import sys
import unittest

CODE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from estimation import CapacityInputs, estimate, validate_latency_budget


class EstimationTests(unittest.TestCase):
    def test_blog_example(self) -> None:
        result = estimate(CapacityInputs())

        self.assertAlmostEqual(result.average_rps, 1_157.407, places=3)
        self.assertAlmostEqual(result.peak_rps, 5_787.037, places=3)
        self.assertEqual(result.raw_event_gb_per_day, 300.0)
        self.assertAlmostEqual(result.in_flight_requests, 231.481, places=3)
        self.assertEqual(result.replica_floor, 24)

    def test_headroom_increases_replica_floor(self) -> None:
        result = estimate(CapacityInputs(replica_headroom=1.25))
        self.assertEqual(result.replica_floor, 29)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "daily_decisions"):
            estimate(CapacityInputs(daily_decisions=0))
        with self.assertRaisesRegex(ValueError, "peak_factor"):
            estimate(CapacityInputs(peak_factor=0.5))

    def test_latency_budget_returns_slack(self) -> None:
        slack = validate_latency_budget(
            80,
            gateway=5,
            features=20,
            model=25,
            policy=5,
            network_and_queue=15,
        )
        self.assertEqual(slack, 10)

    def test_latency_budget_rejects_overcommit(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds target"):
            validate_latency_budget(20, features=12, model=15)


if __name__ == "__main__":
    unittest.main()
