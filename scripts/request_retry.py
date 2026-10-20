"""Execution-only retry decisions; no credentials, networking, or result replay."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time


@dataclass(frozen=True)
class RetryPolicy:
    backoff_seconds: tuple = (3, 6, 12, 24, 45)
    jitter_seconds: float = 1.0
    minimum_interval_seconds: float = 1.5

    def record(self):
        return {"max_retries": len(self.backoff_seconds),
                "backoff_seconds": list(self.backoff_seconds),
                "jitter_seconds": self.jitter_seconds,
                "minimum_interval_seconds": self.minimum_interval_seconds,
                "retry_scope": "identical_rejected_request",
                "retry_classification": "shared_pool_429_rejection",
                "retain_rejected_request_reserves": True}

    def delay(self, http_status, details, retries_used, *, random_value=None):
        """Return a delay, or None to stop. Input is sanitized error metadata.

        The caller must have parsed a complete HTTP error with an exact top-level
        shared-pool classification. Never infer retryability from message text.
        A returned delay does not authorize dispatch or release a reservation.
        """
        if (type(http_status) is not int or http_status != 429 or
                type(retries_used) is not int or not 0 <= retries_used < len(self.backoff_seconds) or
                not isinstance(details, dict) or details.get("body_status") != "sanitized" or
                details.get("retry_classification") != "shared_pool_429_rejection"):
            return None
        hint = details.get("retry_after", {})
        if hint.get("state") == "absent":
            minimum = 0
        elif hint.get("state") in {"seconds", "http_date"}:
            minimum = hint.get("seconds")
            if type(minimum) is not int or not 0 <= minimum <= 86400:
                return None
        else:
            return None
        value = random.random() if random_value is None else random_value
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid retry jitter")
        return max(minimum, self.backoff_seconds[retries_used]) + value * self.jitter_seconds


class RequestPacer:
    """Shared sequential dispatch pacing by model, using monotonic time."""
    def __init__(self, interval=1.5, *, clock=time.monotonic, sleep=time.sleep):
        if type(interval) not in (int, float) or not math.isfinite(interval) or interval < 0:
            raise ValueError("Invalid pacing interval")
        self.interval, self.clock, self.sleep = interval, clock, sleep
        self.last = {}

    def wait(self, model):
        if model in self.last:
            remaining = self.last[model] + self.interval - self.clock()
            while remaining > 0:
                self.sleep(remaining)
                remaining = self.last[model] + self.interval - self.clock()
        self.last[model] = self.clock()
