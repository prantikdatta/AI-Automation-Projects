from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.execution import (
    ApplicationExecutionError,
    ApplicationExecutor,
)
from job_search_automation.application.execution_audit import (
    ApplicationExecutionAudit,
)
from job_search_automation.application.n8n_handler import (
    N8nApplicationHandler,
)
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)
from job_search_automation.application.workflow import (
    ApplicationWorkflow,
)
from job_search_automation.models.job import Job


SEPARATOR = "=" * 80

WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://127.0.0.1:5678/webhook-test/job-application",
).strip()


def fail(message: str) -> None:
    raise RuntimeError(message)


def build_synthetic_job() -> Job:
    return Job(
        title="Senior Data Analyst",
        company="Production Validation Company",
        location="Mumbai",
        description=(
            "Synthetic validation job. "
            "Python SQL Power BI analytics."
        ),
        job_url="https://example.com/validation-job-001",
        source="validation",
        provider="validation",
        searched_role="Senior Data Analyst",
        overall_score=90.0,
        final_selection_eligible=True,
        final_selection_bucket="Apply Now",
    )


def build_synthetic_queue_item() -> ApplicationQueueItem:
    return ApplicationQueueItem(
        job_id="production-validation-job-001",
        title="Senior Data Analyst",
        company="Production Validation Company",
        location="Mumbai",
        job_url="https://example.com/validation-job-001",
        provider="validation",
        source="validation",
        searched_role="Senior Data Analyst",
        overall_score=90.0,
        score=90.0,
        selection_bucket="A - Apply Now",
        readiness_decision=ApplicationQueueStatus.READY,
        queue_status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Synthetic production validation item.",
        resume_match_score=90.0,
        created_at="2026-08-16T00:00:00+00:00",
        notes=["SYNTHETIC_VALIDATION_ONLY"],
        application_url=None,
    )


def validate_queue_contract(
    item: ApplicationQueueItem,
) -> None:
    if item.queue_status not in {
        ApplicationQueueStatus.QUEUED,
        ApplicationQueueStatus.TAILORING_REQUIRED,
    }:
        fail(
            "Synthetic queue item is not executable: "
            f"{item.queue_status!r}"
        )


def validate_execution_result(
    result: Any,
    expected_job_id: str,
) -> None:
    if result.job_id != expected_job_id:
        fail(
            f"Unexpected job_id: {result.job_id!r}"
        )

    if result.status != "SUBMITTED":
        fail(
            "Expected SUBMITTED from local n8n, "
            f"received {result.status!r}."
        )

    if not result.message:
        fail("Execution result message is empty.")

    if not isinstance(result.metadata, dict):
        fail(
            "Execution result metadata must be a dictionary."
        )

    if result.metadata.get("executor") != "n8n":
        fail(
            "Execution metadata executor must be 'n8n': "
            f"{result.metadata!r}"
        )


def validate_audit(
    audit: ApplicationExecutionAudit,
) -> None:
    if audit.status != ApplicationExecutionAudit.SUBMITTED:
        fail(
            "Execution audit did not reach SUBMITTED: "
            f"{audit.status!r}"
        )

    payload = audit.to_dict()

    if payload["job_id"] != audit.job_id:
        fail("Audit serialization changed job_id.")

    if payload["status"] != "SUBMITTED":
        fail("Audit serialization changed status.")

    if not isinstance(payload["created_at"], str):
        fail(
            "Audit created_at is not serialized as a string."
        )

    if not isinstance(payload["updated_at"], str):
        fail(
            "Audit updated_at is not serialized as a string."
        )


def main() -> int:
    print(SEPARATOR)
    print("PRODUCTION APPLICATION EXECUTION VALIDATION")
    print(SEPARATOR)
    print()
    print(
        "WARNING: This validation is synthetic and non-destructive."
    )
    print(
        "No real application submission should be connected."
    )
    print()
    print(f"Webhook: {WEBHOOK_URL}")
    print()

    print(
        "[1/5] Building synthetic executable "
        "ApplicationQueueItem"
    )

    item = build_synthetic_queue_item()
    validate_queue_contract(item)

    print(
        "      PASS: synthetic queue item is executable."
    )

    print()
    print(
        "[2/5] Validating ApplicationWorkflow "
        "-> queue contract"
    )

    workflow = ApplicationWorkflow()

    workflow_result = workflow.process(
        [build_synthetic_job()],
        export_to_sheets=False,
    )

    if workflow_result.evaluated != 1:
        fail(
            "Expected 1 evaluated job, "
            f"got {workflow_result.evaluated}."
        )

    if workflow_result.queued != 1:
        fail(
            "Expected 1 queued job, "
            f"got {workflow_result.queued}."
        )

    if len(workflow_result.queue_items) != 1:
        fail(
            "ApplicationWorkflow did not produce exactly "
            "one synthetic queue item."
        )

    workflow_item = workflow_result.queue_items[0]

    if workflow_item.queue_status not in {
        ApplicationQueueStatus.QUEUED,
        ApplicationQueueStatus.TAILORING_REQUIRED,
    }:
        fail(
            "ApplicationWorkflow produced a non-executable "
            "queue status: "
            f"{workflow_item.queue_status!r}"
        )

    print(
        "      PASS: workflow produced an executable "
        "queue item."
    )
    print(
        f"      queue_status: "
        f"{workflow_item.queue_status.value}"
    )

    print()
    print(
        "[3/5] Creating N8nApplicationHandler"
    )

    handler = N8nApplicationHandler(
        webhook_url=WEBHOOK_URL,
    )

    print(
        "      PASS: n8n application handler created."
    )

    print()
    print(
        "[4/5] Executing synthetic item through "
        "ApplicationExecutor -> n8n"
    )

    executor = ApplicationExecutor(
        handler=handler,
    )

    try:
        execution_result = executor.execute(item)

    except ApplicationExecutionError as exc:
        print()
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print(f"ApplicationExecutionError: {exc}")
        return 1

    validate_execution_result(
        execution_result,
        item.job_id,
    )

    print(
        "      PASS: ApplicationExecutor received "
        "valid n8n response."
    )
    print(
        f"      status : {execution_result.status}"
    )
    print(
        f"      message: {execution_result.message}"
    )
    print(
        f"      metadata: {execution_result.metadata}"
    )

    print()
    print(
        "[5/5] Validating ApplicationExecutionAudit"
    )

    audit = ApplicationExecutionAudit(
        job_id=item.job_id,
    )

    audit.mark_ready(
        message="Synthetic execution ready.",
        metadata={
            "executor": "n8n",
            "validation": True,
        },
    )

    audit.mark_submitted(
        message=execution_result.message,
        metadata=execution_result.metadata,
    )

    validate_audit(audit)

    print(
        "      PASS: execution audit reached SUBMITTED."
    )

    print()
    print(SEPARATOR)
    print(
        "PRODUCTION APPLICATION EXECUTION VALIDATION PASSED"
    )
    print(SEPARATOR)
    print()
    print(
        f"status : {execution_result.status}"
    )
    print(
        f"message: {execution_result.message}"
    )
    print(
        f"metadata: {execution_result.metadata}"
    )
    print(
        f"audit   : {audit.status}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())