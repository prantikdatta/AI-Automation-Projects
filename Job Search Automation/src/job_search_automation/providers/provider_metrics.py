from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import TypedDict


class ProviderMetric(TypedDict):
    success: int
    failure: int
    jobs: int
    time: float


class ProviderMetrics:
    _lock = Lock()

    _metrics: defaultdict[str, ProviderMetric] = defaultdict(
        lambda: {
            "success": 0,
            "failure": 0,
            "jobs": 0,
            "time": 0.0,
        }
    )

    @classmethod
    def record_success(
        cls,
        provider: str,
        jobs: int,
        elapsed: float,
    ) -> None:
        with cls._lock:
            metric = cls._metrics[provider]

            metric["success"] += 1
            metric["jobs"] += jobs
            metric["time"] += elapsed

    @classmethod
    def record_failure(
        cls,
        provider: str,
    ) -> None:
        with cls._lock:
            cls._metrics[provider]["failure"] += 1

    @classmethod
    def snapshot(cls) -> dict[str, ProviderMetric]:
        with cls._lock:
            return dict(cls._metrics)