from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)


@dataclass(frozen=True)
class ApplicationExecutionResult:
    """
    Result of attempting to execute one application-queue item.

    Execution is intentionally adapter-based. The application layer does
    not know whether the eventual executor is a browser, API, n8n workflow,
    or another external automation service.
    """

    job_id: str
    status: str
    message: str
    executed_at: datetime
    metadata: dict[str, Any]


class ApplicationExecutionError(RuntimeError):
    """Raised when application execution fails."""


class ApplicationExecutor:
    """
    Production boundary for application execution.

    The executor accepts one ApplicationQueueItem and delegates the actual
    external application action to an injected callable.

    This keeps browser/API/n8n implementation details outside the core
    application orchestration layer.
    """

    def __init__(
        self,
        handler: Callable[[ApplicationQueueItem], dict[str, Any]] | None = None,
    ) -> None:
        self._handler = handler

    @staticmethod
    def _is_executable(
        item: ApplicationQueueItem,
    ) -> bool:
        """
        Determine whether the queue item is eligible for execution.

        The authoritative operational state is queue_status.

        ApplicationQueueEngine currently maps:
            READY -> QUEUED
            READY_WITH_TAILORING -> TAILORING_REQUIRED

        MANUAL_REVIEW and REJECTED are never executable.
        """

        return item.queue_status in {
            ApplicationQueueStatus.QUEUED,
            ApplicationQueueStatus.TAILORING_REQUIRED,
        }

    def execute(
        self,
        item: ApplicationQueueItem,
    ) -> ApplicationExecutionResult:
        if not isinstance(item, ApplicationQueueItem):
            raise TypeError(
                "item must be an ApplicationQueueItem"
            )

        if not self._is_executable(item):
            raise ApplicationExecutionError(
                (
                    f"Application queue item '{item.job_id}' "
                    f"is not eligible for execution. "
                    f"queue_status={item.queue_status.value!r}."
                )
            )

        if self._handler is None:
            return ApplicationExecutionResult(
                job_id=item.job_id,
                status="READY",
                message=(
                    "Application executor is ready; "
                    "no external handler configured."
                ),
                executed_at=datetime.now(timezone.utc),
                metadata={
                    "queue_status": item.queue_status.value,
                    "readiness_decision": (
                        item.readiness_decision.value
                    ),
                },
            )

        try:
            result = self._handler(item)

            if result is None:
                result = {}

            if not isinstance(result, dict):
                raise TypeError(
                    "Application handler must return a dictionary."
                )

            status = str(
                result.get(
                    "status",
                    "SUBMITTED",
                )
            ).upper()

            message = str(
                result.get(
                    "message",
                    "Application execution completed.",
                )
            )

            metadata = dict(
                result.get(
                    "metadata",
                    {},
                )
            )

            return ApplicationExecutionResult(
                job_id=item.job_id,
                status=status,
                message=message,
                executed_at=datetime.now(timezone.utc),
                metadata=metadata,
            )

        except Exception as exc:
            raise ApplicationExecutionError(
                (
                    f"Application execution failed "
                    f"for '{item.job_id}': {exc}"
                )
            ) from exc

    def execute_many(
        self,
        items: Iterable[ApplicationQueueItem],
    ) -> list[ApplicationExecutionResult]:
        results: list[ApplicationExecutionResult] = []

        for item in items:
            try:
                results.append(
                    self.execute(item)
                )

            except ApplicationExecutionError as exc:
                results.append(
                    ApplicationExecutionResult(
                        job_id=item.job_id,
                        status="FAILED",
                        message=str(exc),
                        executed_at=datetime.now(timezone.utc),
                        metadata={},
                    )
                )

        return results