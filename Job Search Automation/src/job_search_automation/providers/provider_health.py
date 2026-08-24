from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from threading import Lock


MAX_FAILURES = 3

COOLDOWN_MINUTES = 15


class ProviderHealth:
    """
    Tracks provider failures.

    After repeated failures the provider
    enters a cooldown period.

    This prevents repeatedly calling
    providers that are temporarily unavailable.
    """

    _failures: dict[str, int] = {}

    _cooldown_until: dict[str, datetime] = {}

    _lock = Lock()

    @classmethod
    def available(
        cls,
        provider: str,
    ) -> bool:

        with cls._lock:

            cooldown = cls._cooldown_until.get(
                provider,
            )

            if cooldown is None:

                return True

            return datetime.now(
                timezone.utc,
            ) >= cooldown

    @classmethod
    def success(
        cls,
        provider: str,
    ) -> None:

        with cls._lock:

            cls._failures.pop(
                provider,
                None,
            )

            cls._cooldown_until.pop(
                provider,
                None,
            )

    @classmethod
    def failure(
        cls,
        provider: str,
    ) -> None:

        with cls._lock:

            failures = (

                cls._failures.get(
                    provider,
                    0,
                )

                + 1

            )

            cls._failures[provider] = failures

            if failures >= MAX_FAILURES:

                cls._cooldown_until[provider] = (

                    datetime.now(
                        timezone.utc,
                    )

                    + timedelta(
                        minutes=COOLDOWN_MINUTES,
                    )

                )

                cls._failures[provider] = 0