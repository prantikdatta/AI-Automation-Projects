from __future__ import annotations

from job_search_automation.application.queue import (
    ApplicationQueueStatus,
)
from job_search_automation.application.queue_builder import (
    ApplicationQueueBuilder,
)
from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)
from job_search_automation.application.workflow import (
    ApplicationWorkflow,
)
from job_search_automation.models.job import Job


class FakeSheetsWriter:
    def __init__(self) -> None:
        self.headers: list[str] = []
        self.rows: list[list[str]] = []

    def append_application_queue(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> None:
        self.headers = list(headers)
        self.rows = [
            list(row)
            for row in rows
        ]


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def build_job(
    *,
    title: str,
    score: float,
) -> Job:
    job = Job(
        title=title,
        company="Test Company",
        location="Mumbai",
        description=(
            "Data analytics role involving SQL, "
            "Power BI, reporting and stakeholder management."
        ),
        job_url=(
            "https://example.com/"
            + title.lower().replace(" ", "-")
            + f"-{score}"
        ),
        source="test",
        searched_role=title,
        provider="test",
    )

    job.overall_score = score
    job.final_selection_eligible = True
    job.final_selection_bucket = "C - Review"
    job.final_selection_priority = 1

    return job


def main() -> None:
    print("=" * 80)
    print("APPLICATION WORKFLOW VALIDATION")
    print("=" * 80)

    writer = FakeSheetsWriter()

    exporter = ApplicationQueueSheetsExporter(
        writer
    )

    queue_builder = ApplicationQueueBuilder()

    workflow = ApplicationWorkflow(
        queue_builder=queue_builder,
        sheets_exporter=exporter,
    )

    jobs = [
        build_job(
            title="Senior Data Analyst",
            score=75.0,
        ),
        build_job(
            title="Senior Data Analyst",
            score=65.0,
        ),
        build_job(
            title="Senior Data Analyst",
            score=40.0,
        ),
    ]

    result = workflow.process(
        jobs,
        export_to_sheets=True,
    )

    require(
        result.evaluated == 3,
        "Expected three jobs to be evaluated.",
    )

    require(
        len(result.queue_items) == 2,
        (
            "Expected two eligible ApplicationQueueItem objects; "
            f"got {len(result.queue_items)}."
        ),
    )

    require(
        result.queued == 2,
        (
            "Expected two actionable queue items; "
            f"got {result.queued}."
        ),
    )

    require(
        result.manual_review == 0,
        (
            "Manual-review jobs should not enter the queue builder; "
            f"got {result.manual_review}."
        ),
    )

    require(
        result.rejected == 0,
        (
            "Rejected jobs should not enter the queue builder; "
            f"got {result.rejected}."
        ),
    )

    require(
        len(writer.rows) == 2,
        (
            "Only actionable jobs should reach Sheets; "
            f"got {len(writer.rows)} rows."
        ),
    )

    require(
        len(writer.headers) > 0,
        "Application Queue headers were not written.",
    )

    for row in writer.rows:
        require(
            len(row) == len(writer.headers),
            "Application Queue row/header mismatch.",
        )

    statuses = {
        item.queue_status
        for item in result.queue_items
    }

    require(
        ApplicationQueueStatus.QUEUED in statuses,
        "READY job did not enter QUEUED status.",
    )

    require(
        ApplicationQueueStatus.TAILORING_REQUIRED in statuses,
        "Tailoring job did not enter TAILORING_REQUIRED status.",
    )

    print("PASS | final-selected jobs processed")
    print(f"PASS | evaluated={result.evaluated}")
    print(f"PASS | queue items={len(result.queue_items)}")
    print(f"PASS | queued={result.queued}")
    print(f"PASS | manual_review={result.manual_review}")
    print(f"PASS | rejected={result.rejected}")
    print(f"PASS | Sheets rows={len(writer.rows)}")

    print("=" * 80)
    print("APPLICATION WORKFLOW VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()