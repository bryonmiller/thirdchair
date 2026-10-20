"""Retry decisions and pacing use synthetic clocks and metadata only."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from request_retry import RequestPacer, RetryPolicy


def rejection(hint=None):
    return {"body_status": "sanitized", "retry_classification": "shared_pool_429_rejection",
            "retry_after": hint or {"state": "absent"}}


class RetryTests(unittest.TestCase):
    def test_five_retries_then_exhaustion(self):
        policy = RetryPolicy()
        self.assertEqual([policy.delay(429, rejection(), n, random_value=0.5)
                          for n in range(5)], [3.5, 6.5, 12.5, 24.5, 45.5])
        self.assertIsNone(policy.delay(429, rejection(), 5))

    def test_retry_after_is_a_lower_bound(self):
        for mode in ("seconds", "http_date"):
            self.assertEqual(RetryPolicy().delay(429, rejection({"state": mode, "seconds": 60}),
                                                0, random_value=0), 60)

    def test_no_retry_for_unknown_auth_billing_transport_or_malformed_response(self):
        for code in (400, 401, 402, 403, 408, 500, 503, None, True):
            self.assertIsNone(RetryPolicy().delay(code, rejection(), 0))
        for detail in ({}, {"body_status": "redacted"},
                       {**rejection(), "retry_classification": "other"},
                       {**rejection(), "retry_after": {"state": "invalid"}},
                       rejection({"state": "seconds", "seconds": True})):
            self.assertIsNone(RetryPolicy().delay(429, detail, 0))

    def test_shared_pacing_and_no_unnecessary_sleep(self):
        clock = [0.0]; waits = []
        def sleep(seconds):
            waits.append(seconds); clock[0] += seconds
        pace = RequestPacer(clock=lambda: clock[0], sleep=sleep)
        pace.wait("A"); pace.wait("B"); pace.wait("A")
        self.assertEqual(waits, [1.5])
        clock[0] += 10
        pace.wait("A")
        self.assertEqual(waits, [1.5])

    def test_invalid_clock_configuration_and_jitter_rejected(self):
        for value in (-1, float("nan"), True):
            with self.assertRaises(ValueError): RequestPacer(value)
        with self.assertRaises(ValueError):
            RetryPolicy().delay(429, rejection(), 0, random_value=float("nan"))
