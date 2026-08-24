from __future__ import annotations

from typing import Any

from job_search_automation.application.decision import (
    ApplicationDecision,
)
from job_search_automation.application.queue import (
    ApplicationQueueEngine,
    ApplicationQueueStatus,
)
from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)
from job_search_automation.application.readiness import (
    ApplicationReadinessEngine,
)
from job_search_automation.models.job import Job


class FakeSheetsWriter:
    """
    In-memory Sheets writer.

    No Google API calls are made.
    """

    def __init__(self) -> None:
        self.headers: list[str] = []
        self.rows: list[list[str]] = []

    def append_application_queue(
        self,
        *,
        headers: list[str],
        rows: list[list[str]],
    ) -> Any:
        self.headers = list(headers)
        self.rows = [list(row) for row in rows]

        return True


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def build_job(
    score: float,
) -> Job:
    job = Job(
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        description=(
            "Senior Data Analyst responsible for SQL, "
            "analytics, BI, reporting and stakeholder management."
        ),
        job_url="https://example.com/job/123",
        source="test",
        searched_role="Senior Data Analyst",
        provider="test",
    )

    job.overall_score = score
    job.final_selection_eligible = True
    job.final_selection_bucket = "C - Review"

    return job


def main() -> None:
    print("=" * 80)
    print("APPLICATION QUEUE SHEETS VALIDATION")
    print("=" * 80)

    readiness_engine = ApplicationReadinessEngine()
    queue_engine = ApplicationQueueEngine()

    writer = FakeSheetsWriter()
    exporter = ApplicationQueueSheetsExporter(writer)

    # ----------------------------------------------------------
    # READY
    # ----------------------------------------------------------

    job = build_job(75.0)

    readiness = readiness_engine.evaluate(job)
    item = queue_engine.build(
        job,
        readiness,
    )

    require(
        readiness.decision == ApplicationDecision.READY,
        "Expected READY decision.",
    )

    require(
        item.queue_status == ApplicationQueueStatus.QUEUED,
        "Expected QUEUED status.",
    )

    exported = exporter.export([item])

    require(
        exported == 1,
        "Exactly one queue row should be exported.",
    )

    require(
        len(writer.rows) == 1,
        "Sheets writer should receive exactly one row.",
    )

    require(
        len(writer.headers) == len(writer.rows[0]),
        "Headers and row column counts must match.",
    )

    print("PASS | READY item exported")

    # ----------------------------------------------------------
    # MULTIPLE QUEUE ITEMS
    # ----------------------------------------------------------

    jobs = [
        build_job(75.0),
        build_job(65.0),
    ]

    readiness_items = []

    for job in jobs:
        readiness = readiness_engine.evaluate(job)
        readiness_items.append(
            queue_engine.build(
                job,
                readiness,
            )
        )

    writer = FakeSheetsWriter()
    exporter = ApplicationQueueSheetsExporter(writer)

    exported = exporter.export(
        readiness_items,
    )

    require(
        exported == 2,
        "Two queue items should produce two rows.",
    )

    require(
        len(writer.rows) == 2,
        "Sheets writer should receive two rows.",
    )

    print("PASS | multiple queue items exported")

    # ----------------------------------------------------------
    # EMPTY QUEUE
    # ----------------------------------------------------------

    writer = FakeSheetsWriter()
    exporter = ApplicationQueueSheetsExporter(writer)

    exported = exporter.export([])

    require(
        exported == 0,
        "Empty queue must export zero rows.",
    )

    require(
        writer.rows == [],
        "Empty queue must not call the writer.",
    )

    print("PASS | empty queue produces no Sheets write")

    # ----------------------------------------------------------
    # RESULT
    # ----------------------------------------------------------

    print("=" * 80)
    print("APPLICATION QUEUE SHEETS VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()