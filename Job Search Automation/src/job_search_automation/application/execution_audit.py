from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from job_search_automation.application.execution import (
    ApplicationExecutionResult,
)


class ApplicationExecutionAuditError(RuntimeError):
    """Raised when an invalid execution-audit transition occurs."""


@dataclass
class ApplicationExecutionAudit:
    """
    Persistent audit state for one application execution attempt.

    The audit records execution lifecycle only.

    Lifecycle:

        NOT_STARTED
             ↓
           READY
             ↓
        SUBMITTED

    Failure can occur from NOT_STARTED or READY:

        NOT_STARTED / READY
                ↓
             FAILED

    This class does not execute applications and does not contain
    browser, API, or n8n-specific logic.
    """

    job_id: str
    status: str = "NOT_STARTED"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # STATUS CONSTANTS
    # ==========================================================

    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"

    VALID_STATUSES = {
        NOT_STARTED,
        READY,
        SUBMITTED,
        FAILED,
    }

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __post_init__(self) -> None:
        if not self.job_id:
            raise ValueError("job_id must not be empty.")

        self.status = str(self.status).upper()

        if self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid application execution status {self.status!r}."
            )

        self.metadata = dict(self.metadata)

    # ==========================================================
    # STATE TRANSITIONS
    # ==========================================================

    def mark_ready(
        self,
        *,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an execution as ready to be handed to an executor."""

        self._transition(
            expected_statuses={self.NOT_STARTED},
            new_status=self.READY,
            message=message,
            metadata=metadata,
        )

    def mark_submitted(
        self,
        *,
        message: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an application as successfully submitted."""

        self._transition(
            expected_statuses={self.READY},
            new_status=self.SUBMITTED,
            message=message,
            metadata=metadata,
        )

    def mark_failed(
        self,
        *,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an application execution as failed."""

        self._transition(
            expected_statuses={
                self.NOT_STARTED,
                self.READY,
            },
            new_status=self.FAILED,
            message=message,
            metadata=metadata,
        )

    # ==========================================================
    # TRANSITION ENGINE
    # ==========================================================

    def _transition(
        self,
        *,
        expected_statuses: set[str],
        new_status: str,
        message: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        if self.status not in expected_statuses:
            raise ApplicationExecutionAuditError(
                (
                    f"Invalid execution-audit transition for "
                    f"job '{self.job_id}': "
                    f"{self.status!r} -> {new_status!r}."
                )
            )

        self.status = new_status
        self.message = message or ""

        if metadata is not None:
            self.metadata.update(metadata)

        self.updated_at = datetime.now(timezone.utc)

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self) -> dict[str, Any]:
        """Return a stable serialization for audit persistence/export."""

        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message": self.message,
            "metadata": dict(self.metadata),
        }


class ApplicationExecutionAuditStore:
    """
    In-memory audit store for application execution results.

    The store is deliberately persistence-agnostic. It provides the
    application layer with a deterministic audit boundary that can later
    be backed by a database, Google Sheets, n8n, or another persistence
    mechanism without changing execution orchestration.
    """

    def __init__(self) -> None:
        self._records: dict[str, ApplicationExecutionAudit] = {}

    # ==========================================================
    # RECORDING
    # ==========================================================

    def record(
        self,
        result: ApplicationExecutionResult,
        *,
        executor: str | None = None,
    ) -> ApplicationExecutionAudit:
        """
        Record one application execution result.

        SUBMITTED results are recorded as SUBMITTED.
        FAILED results are recorded as FAILED.
        READY results are recorded as READY.
        """

        if not isinstance(
            result,
            ApplicationExecutionResult,
        ):
            raise TypeError(
                "result must be an ApplicationExecutionResult."
            )

        status = str(result.status).upper()

        if status not in {
            ApplicationExecutionAudit.READY,
            ApplicationExecutionAudit.SUBMITTED,
            ApplicationExecutionAudit.FAILED,
        }:
            raise ApplicationExecutionAuditError(
                (
                    f"Unsupported execution result status "
                    f"{result.status!r} for job "
                    f"'{result.job_id}'."
                )
            )

        audit = ApplicationExecutionAudit(
            job_id=result.job_id,
        )

        if status == ApplicationExecutionAudit.READY:
            audit.mark_ready(
                message=result.message,
                metadata=result.metadata,
            )

        elif status == ApplicationExecutionAudit.SUBMITTED:
            audit.mark_ready(
                message="Execution became ready.",
                metadata=result.metadata,
            )
            audit.mark_submitted(
                message=result.message,
                metadata=result.metadata,
            )

        elif status == ApplicationExecutionAudit.FAILED:
            audit.mark_failed(
                message=result.message,
                metadata=result.metadata,
            )

        if executor:
            audit.metadata["executor"] = executor

        audit.metadata["executed_at"] = (
            result.executed_at.isoformat()
        )

        self._records[result.job_id] = audit

        return audit

    def record_many(
        self,
        results: Iterable[ApplicationExecutionResult],
        *,
        executor: str | None = None,
    ) -> list[ApplicationExecutionAudit]:
        """Record multiple execution results."""

        return [
            self.record(
                result,
                executor=executor,
            )
            for result in results
        ]

    # ==========================================================
    # RETRIEVAL
    # ==========================================================

    def get(
        self,
        job_id: str,
    ) -> ApplicationExecutionAudit | None:
        """Return an audit record by job ID."""

        return self._records.get(job_id)

    def all(
        self,
    ) -> list[ApplicationExecutionAudit]:
        """Return all audit records."""

        return list(self._records.values())

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def summary(self) -> dict[str, int]:
        """Return execution counts grouped by audit status."""

        summary: dict[str, int] = {}

        for audit in self._records.values():
            summary[audit.status] = (
                summary.get(audit.status, 0) + 1
            )

        return summary

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self) -> None:
        """Remove all audit records."""

        self._records.clear()