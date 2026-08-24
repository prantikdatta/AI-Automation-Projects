from __future__ import annotations

from job_search_automation.application.decision import (
    ApplicationDecision,
)
from job_search_automation.application.queue import (
    ApplicationQueueEngine,
    ApplicationQueueStatus,
)
from job_search_automation.application.queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
    application_queue_rows,
)
from job_search_automation.application.readiness import (
    ApplicationReadinessEngine,
)
from job_search_automation.models.job import Job


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
    print("APPLICATION QUEUE MAPPER VALIDATION")
    print("=" * 80)

    readiness_engine = ApplicationReadinessEngine()
    queue_engine = ApplicationQueueEngine()

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

    rows = application_queue_rows([item])

    require(
        len(rows) == 1,
        "Exactly one queue row should be produced.",
    )

    row = rows[0]

    require(
        len(row) == len(APPLICATION_QUEUE_HEADERS),
        (
            "Queue row/header length mismatch: "
            f"{len(row)} != {len(APPLICATION_QUEUE_HEADERS)}"
        ),
    )

    require(
        row[1] == item.job_id,
        "Job ID was not mapped correctly.",
    )

    require(
        row[4] == item.company,
        "Company was not mapped correctly.",
    )

    require(
        row[5] == item.title,
        "Role/title was not mapped correctly.",
    )

    require(
        row[6] == item.location,
        "Location was not mapped correctly.",
    )

    require(
        row[7] == item.job_url,
        "Job URL was not mapped correctly.",
    )

    require(
        row[8] == "75.00",
        "Overall score was not mapped correctly.",
    )

    require(
        row[10] == "READY",
        "Readiness decision was not mapped correctly.",
    )

    require(
        row[11] == "QUEUED",
        "Queue status was not mapped correctly.",
    )

    require(
        row[12] == "TRUE",
        "Eligibility was not mapped correctly.",
    )

    print("PASS | READY queue item mapped")

    # ----------------------------------------------------------
    # TAILORING
    # ----------------------------------------------------------

    job = build_job(65.0)

    readiness = readiness_engine.evaluate(job)
    item = queue_engine.build(
        job,
        readiness,
    )

    rows = application_queue_rows([item])
    row = rows[0]

    require(
        row[10] == "READY_WITH_TAILORING",
        "Tailoring decision was not mapped correctly.",
    )

    require(
        row[11] == "TAILORING_REQUIRED",
        "Tailoring queue status was not mapped correctly.",
    )

    require(
        row[13] == "TRUE",
        "Tailoring flag was not mapped correctly.",
    )

    print("PASS | READY_WITH_TAILORING queue item mapped")

    # ----------------------------------------------------------
    # MANUAL REVIEW
    # ----------------------------------------------------------

    job = build_job(57.75)

    readiness = readiness_engine.evaluate(job)
    item = queue_engine.build(
        job,
        readiness,
    )

    rows = application_queue_rows([item])
    row = rows[0]

    require(
        row[10] == "MANUAL_REVIEW",
        "Manual-review decision was not mapped correctly.",
    )

    require(
        row[11] == "MANUAL_REVIEW",
        "Manual-review queue status was not mapped correctly.",
    )

    require(
        row[12] == "FALSE",
        "Manual-review eligibility was not mapped correctly.",
    )

    print("PASS | MANUAL_REVIEW queue item mapped")

    # ----------------------------------------------------------
    # REJECTED
    # ----------------------------------------------------------

    job = build_job(90.0)
    job.final_selection_eligible = False

    readiness = readiness_engine.evaluate(job)
    item = queue_engine.build(
        job,
        readiness,
    )

    rows = application_queue_rows([item])
    row = rows[0]

    require(
        row[10] == "REJECTED",
        "Rejected decision was not mapped correctly.",
    )

    require(
        row[11] == "REJECTED",
        "Rejected queue status was not mapped correctly.",
    )

    require(
        row[12] == "FALSE",
        "Rejected eligibility was not mapped correctly.",
    )

    print("PASS | REJECTED queue item mapped")

    print("=" * 80)
    print("APPLICATION QUEUE MAPPER VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()