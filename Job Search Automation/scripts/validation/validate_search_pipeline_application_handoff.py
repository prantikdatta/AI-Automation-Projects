from __future__ import annotations

from unittest.mock import MagicMock, patch

from job_search_automation.application.workflow import (
    ApplicationWorkflow,
    ApplicationWorkflowResult,
)
from job_search_automation.models.job import Job
from job_search_automation.orchestrators.search_pipeline import (
    SearchPipeline,
)


def build_selected_job() -> MagicMock:
    job = MagicMock(spec=Job)

    job.title = "Data Analyst"
    job.company = "Validation Company"
    job.location = "Mumbai"
    job.job_url = "https://example.com/jobs/validation"
    job.description = "Data analysis and BI role."
    job.final_selection_eligible = True
    job.final_selection_bucket = "STRONG_MATCH"
    job.overall_score = 85.0

    return job


class OfflineQueueExporter:
    def __init__(self) -> None:
        self.calls = 0
        self.items = []

    def export(self, items) -> int:
        self.calls += 1
        self.items = list(items)
        return len(self.items)


def main() -> None:
    print("=" * 90)
    print("SEARCH PIPELINE → APPLICATION WORKFLOW HANDOFF VALIDATION")
    print("=" * 90)
    print("Mode        : OFFLINE")
    print("Apify calls : 0")
    print("RapidAPI    : 0")
    print("Gemini      : 0")
    print("Sheets API  : 0")
    print("n8n calls   : 0")
    print("Applications: 0")
    print()

    # ----------------------------------------------------------
    # 1. SearchPipeline construction
    # ----------------------------------------------------------

    print("[1/4] SearchPipeline construction")

    with patch(
        "job_search_automation.orchestrators.search_pipeline.GoogleSheetsService"
    ) as sheets_service_class:

        sheets_service = MagicMock()
        sheets_service_class.return_value = sheets_service

        pipeline = SearchPipeline()

    if not isinstance(
        pipeline.application_workflow,
        ApplicationWorkflow,
    ):
        raise AssertionError(
            "SearchPipeline.application_workflow is not "
            "an ApplicationWorkflow instance."
        )

    if not hasattr(
        pipeline,
        "application_queue_exporter",
    ):
        raise AssertionError(
            "SearchPipeline is missing "
            "application_queue_exporter."
        )

    print("      PASS")

    # ----------------------------------------------------------
    # 2. Application Workflow handoff
    # ----------------------------------------------------------

    print("[2/4] Application Workflow handoff")

    exporter = OfflineQueueExporter()

    workflow = ApplicationWorkflow(
        sheets_exporter=exporter,
    )

    job = build_selected_job()

    result = workflow.process(
        [job],
        export_to_sheets=True,
    )

    if not isinstance(
        result,
        ApplicationWorkflowResult,
    ):
        raise AssertionError(
            "ApplicationWorkflow did not return "
            "ApplicationWorkflowResult."
        )

    if result.evaluated != 1:
        raise AssertionError(
            f"Expected evaluated=1; "
            f"found {result.evaluated}."
        )

    print("      PASS")

    # ----------------------------------------------------------
    # 3. Actionable queue export boundary
    # ----------------------------------------------------------

    print("[3/4] Actionable queue export boundary")

    if exporter.calls != 1:
        raise AssertionError(
            "Expected exactly one queue export call; "
            f"found {exporter.calls}."
        )

    if result.queued != 1:
        raise AssertionError(
            f"Expected queued=1; "
            f"found {result.queued}."
        )

    if len(exporter.items) != 1:
        raise AssertionError(
            "Expected exactly one actionable queue item."
        )

    queue_item = exporter.items[0]

    status = getattr(
        queue_item,
        "queue_status",
        None,
    )

    status_value = getattr(
        status,
        "value",
        status,
    )

    if str(status_value).upper() not in {
        "READY",
        "READY_WITH_TAILORING",
    }:
        raise AssertionError(
            "Exported queue item is not actionable: "
            f"{status_value!r}."
        )

    print("      PASS")

    # ----------------------------------------------------------
    # 4. SearchPipeline dependency boundary
    # ----------------------------------------------------------

    print("[4/4] SearchPipeline dependency boundary")

    if not hasattr(
        pipeline,
        "application_workflow",
    ):
        raise AssertionError(
            "SearchPipeline is missing "
            "application_workflow."
        )

    if not hasattr(
        pipeline,
        "application_queue_exporter",
    ):
        raise AssertionError(
            "SearchPipeline is missing "
            "application_queue_exporter."
        )

    if (
        pipeline.application_workflow.sheets_exporter
        is not pipeline.application_queue_exporter
    ):
        raise AssertionError(
            "ApplicationWorkflow is not wired to "
            "ApplicationQueueSheetsExporter."
        )

    print("      PASS")

    print()
    print("=" * 90)
    print(
        "SEARCH PIPELINE → APPLICATION WORKFLOW "
        "HANDOFF VALIDATION PASSED"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()