from __future__ import annotations

from job_search_automation.application.queue import (
    ApplicationQueueStatus,
)
from job_search_automation.application.workflow import (
    ApplicationWorkflow,
    ApplicationWorkflowResult,
)
from job_search_automation.models.job import Job


def make_job(
    score: float,
    eligible: bool = True,
) -> Job:
    return Job(
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        description="Python SQL Power BI analytics.",
        job_url=f"https://example.com/job/{score}",
        source="test",
        provider="test",
        searched_role="Senior Data Analyst",
        overall_score=score,
        final_selection_eligible=eligible,
        final_selection_bucket="Apply Now",
    )


class FakeSheetsExporter:
    def __init__(self) -> None:
        self.exported_items = []

    def append_items(self, items) -> None:
        self.exported_items.append(list(items))


def test_workflow_processes_eligible_jobs() -> None:
    workflow = ApplicationWorkflow()

    result = workflow.process(
        [
            make_job(85),
        ],
        export_to_sheets=False,
    )

    assert isinstance(
        result,
        ApplicationWorkflowResult,
    )

    assert result.evaluated == 1
    assert result.queued == 1
    assert result.manual_review == 0
    assert result.rejected == 0

    assert len(result.queue_items) == 1
    assert (
        result.queue_items[0].queue_status
        == ApplicationQueueStatus.QUEUED
    )


def test_workflow_excludes_ineligible_jobs() -> None:
    workflow = ApplicationWorkflow()

    result = workflow.process(
        [
            make_job(
                85,
                eligible=False,
            ),
        ],
        export_to_sheets=False,
    )

    assert result.evaluated == 1
    assert result.queued == 0
    assert result.manual_review == 0
    assert result.rejected == 0
    assert result.queue_items == []


def test_workflow_counts_tailoring_as_queued() -> None:
    workflow = ApplicationWorkflow()

    result = workflow.process(
        [
            make_job(65),
        ],
        export_to_sheets=False,
    )

    assert result.evaluated == 1
    assert result.queued == 1
    assert result.manual_review == 0
    assert result.rejected == 0

    assert (
        result.queue_items[0].queue_status
        == ApplicationQueueStatus.TAILORING_REQUIRED
    )


def test_workflow_preserves_queue_items() -> None:
    workflow = ApplicationWorkflow()

    result = workflow.process(
        [
            make_job(85),
            make_job(65),
        ],
        export_to_sheets=False,
    )

    assert result.evaluated == 2
    assert result.queued == 2
    assert len(result.queue_items) == 2

    assert (
        result.queue_items[0].queue_status
        == ApplicationQueueStatus.QUEUED
    )

    assert (
        result.queue_items[1].queue_status
        == ApplicationQueueStatus.TAILORING_REQUIRED
    )


def test_workflow_does_not_export_when_disabled() -> None:
    exporter = FakeSheetsExporter()

    workflow = ApplicationWorkflow(
        sheets_exporter=exporter,
    )

    result = workflow.process(
        [
            make_job(85),
        ],
        export_to_sheets=False,
    )

    assert result.queued == 1
    assert exporter.exported_items == []


def test_workflow_exports_actionable_items() -> None:
    exporter = FakeSheetsExporter()

    workflow = ApplicationWorkflow(
        sheets_exporter=exporter,
    )

    result = workflow.process(
        [
            make_job(85),
            make_job(65),
        ],
        export_to_sheets=True,
    )

    assert result.queued == 2
    assert len(exporter.exported_items) == 1

    exported = exporter.exported_items[0]

    assert len(exported) == 2
    assert all(
        item.queue_status
        in {
            ApplicationQueueStatus.QUEUED,
            ApplicationQueueStatus.TAILORING_REQUIRED,
        }
        for item in exported
    )


def test_workflow_does_not_export_when_no_actionable_items() -> None:
    exporter = FakeSheetsExporter()

    workflow = ApplicationWorkflow(
        sheets_exporter=exporter,
    )

    result = workflow.process(
        [
            make_job(
                85,
                eligible=False,
            ),
        ],
        export_to_sheets=True,
    )

    assert result.evaluated == 1
    assert result.queued == 0
    assert result.queue_items == []
    assert exporter.exported_items == []