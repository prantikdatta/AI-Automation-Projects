from __future__ import annotations

from dataclasses import dataclass

from job_search_automation.application.queue import (
    ApplicationQueueItem,
)
from job_search_automation.application.queue_builder import (
    ApplicationQueueBuilder,
)
from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)
from job_search_automation.models.job import Job


@dataclass(slots=True)
class ApplicationWorkflowResult:
    """
    Result produced by the application workflow.
    """

    evaluated: int
    queued: int
    manual_review: int
    rejected: int
    queue_items: list[ApplicationQueueItem]


class ApplicationWorkflow:
    """
    Coordinates the application workflow.

    Flow:

        Final Selection
            ↓
        ApplicationQueueBuilder
            ↓
        Application Queue
            ↓
        Optional Sheets export

    ApplicationQueueBuilder owns the readiness decision.

    This workflow does NOT:

        - search providers
        - score jobs
        - call Gemini
        - modify resumes
        - submit applications
    """

    def __init__(
        self,
        queue_builder: ApplicationQueueBuilder | None = None,
        sheets_exporter: ApplicationQueueSheetsExporter | None = None,
    ) -> None:
        self.queue_builder = (
            queue_builder
            or ApplicationQueueBuilder()
        )

        self.sheets_exporter = sheets_exporter

    def process(
        self,
        jobs: list[Job],
        *,
        export_to_sheets: bool = True,
    ) -> ApplicationWorkflowResult:
        """
        Convert final-selected jobs into application
        queue items.
        """

        queue_items = self.queue_builder.build(jobs)

        queued = sum(
            1
            for item in queue_items
            if self._is_actionable(item)
        )

        manual_review = sum(
            1
            for item in queue_items
            if self._status(item) == "MANUAL_REVIEW"
        )

        rejected = sum(
            1
            for item in queue_items
            if self._status(item) == "REJECTED"
        )

        actionable_items = [
            item
            for item in queue_items
            if self._is_actionable(item)
        ]

        if (
            export_to_sheets
            and self.sheets_exporter is not None
            and actionable_items
        ):
            self.sheets_exporter.append_items(
                actionable_items
            )

        return ApplicationWorkflowResult(
            evaluated=len(jobs),
            queued=queued,
            manual_review=manual_review,
            rejected=rejected,
            queue_items=queue_items,
        )

    @staticmethod
    def _status(
        item: ApplicationQueueItem,
    ) -> str:
        """
        Read the canonical queue_status field.
        """

        status = getattr(
            item,
            "queue_status",
            None,
        )

        value = getattr(
            status,
            "value",
            status,
        )

        return str(
            value or ""
        ).upper()

    @classmethod
    def _is_actionable(
        cls,
        item: ApplicationQueueItem,
    ) -> bool:
        """
        Determine whether a queue item is actionable.

        MANUAL_REVIEW and REJECTED are excluded.
        """

        return cls._status(item) in {
            "READY",
            "READY_WITH_TAILORING",
        }