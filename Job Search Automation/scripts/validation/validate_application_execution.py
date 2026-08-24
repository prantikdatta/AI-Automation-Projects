from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from job_search_automation.application.execution import (
    ApplicationExecutionError,
    ApplicationExecutionResult,
    ApplicationExecutor,
)
from job_search_automation.application.execution_audit import (
    ApplicationExecutionAuditStore,
)
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)


class ValidationFailure(AssertionError):
    """Raised when an application-execution invariant fails."""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise ValidationFailure(message)


def build_queue_item(
    *,
    job_id: str,
    queue_status: ApplicationQueueStatus,
) -> ApplicationQueueItem:
    """
    Construct an ApplicationQueueItem using the current
    production queue contract.
    """

    is_ready = queue_status in {
        ApplicationQueueStatus.READY,
        ApplicationQueueStatus.READY_WITH_TAILORING,
    }

    tailoring_required = (
        queue_status
        == ApplicationQueueStatus.READY_WITH_TAILORING
    )

    return ApplicationQueueItem(
        job_id=job_id,
        title="Senior Data Analyst",
        company="Test Company",
        location="Mumbai",
        job_url=f"https://example.com/{job_id}",
        provider="test",
        source="test",
        searched_role="Data Analyst",
        overall_score=90.0,
        score=90.0,
        selection_bucket="A - Apply Now",
        readiness_decision=(
            "READY_WITH_TAILORING"
            if tailoring_required
            else "READY"
            if is_ready
            else "MANUAL_REVIEW"
        ),
        queue_status=queue_status,
        decision=queue_status,
        status=queue_status,
        eligible=is_ready,
        reason=(
            "Eligible for application."
            if is_ready
            else "Requires manual review."
        ),
        resume_tailoring_required=tailoring_required,
        notes=[],
        recommended_actions=[],
        application_url=None,
    )


def validate_executor_without_handler() -> None:
    print(
        "\n[1/5] Testing QUEUED item "
        "without external handler"
    )

    item = build_queue_item(
        job_id="execution-test-ready",
        queue_status=ApplicationQueueStatus.QUEUED,
    )

    executor = ApplicationExecutor()

    result = executor.execute(item)

    require(
        isinstance(
            result,
            ApplicationExecutionResult,
        ),
        "Executor did not return ApplicationExecutionResult.",
    )

    require(
        result.job_id == "execution-test-ready",
        "Execution result has incorrect job_id.",
    )

    require(
        result.status == "READY",
        f"Expected READY, got {result.status!r}.",
    )

    print(
        "      PASS: QUEUED item accepted "
        "by execution boundary."
    )


def validate_successful_external_execution() -> None:
    print(
        "\n[2/5] Testing successful external execution"
    )

    item = build_queue_item(
        job_id="execution-test-submitted",
        queue_status=ApplicationQueueStatus.QUEUED,
    )

    calls: list[str] = []

    def fake_handler(
        queue_item: ApplicationQueueItem,
    ) -> dict[str, Any]:
        calls.append(queue_item.job_id)

        return {
            "status": "SUBMITTED",
            "message": (
                "Fake application submitted successfully."
            ),
            "metadata": {
                "executor": "fake",
                "test": True,
            },
        }

    executor = ApplicationExecutor(
        handler=fake_handler,
    )

    result = executor.execute(item)

    require(
        result.status == "SUBMITTED",
        f"Expected SUBMITTED, got {result.status!r}.",
    )

    require(
        result.metadata["executor"] == "fake",
        "Executor metadata was not preserved.",
    )

    require(
        calls == ["execution-test-submitted"],
        "Fake handler was not called exactly once.",
    )

    print(
        "      PASS: QUEUED -> SUBMITTED "
        "execution succeeded."
    )


def validate_failed_external_execution() -> None:
    print(
        "\n[3/5] Testing failed external execution"
    )

    item = build_queue_item(
        job_id="execution-test-failed",
        queue_status=ApplicationQueueStatus.QUEUED,
    )

    def failing_handler(
        _: ApplicationQueueItem,
    ) -> dict[str, Any]:
        raise RuntimeError(
            "simulated submission failure"
        )

    executor = ApplicationExecutor(
        handler=failing_handler,
    )

    try:
        executor.execute(item)

    except ApplicationExecutionError as exc:
        require(
            "execution-test-failed" in str(exc),
            "Failure message does not contain job_id.",
        )

        require(
            "simulated submission failure" in str(exc),
            "Original failure is missing from error message.",
        )

        print(
            "      PASS: external failure converted "
            "to ApplicationExecutionError."
        )

        return

    raise ValidationFailure(
        "Expected ApplicationExecutionError was not raised."
    )


def validate_non_executable_item() -> None:
    print(
        "\n[4/5] Testing non-executable queue item"
    )

    item = build_queue_item(
        job_id="execution-test-rejected",
        queue_status=ApplicationQueueStatus.MANUAL_REVIEW,
    )

    executor = ApplicationExecutor()

    try:
        executor.execute(item)

    except ApplicationExecutionError as exc:
        require(
            "execution-test-rejected" in str(exc),
            "Rejected execution error does not contain job_id.",
        )

        print(
            "      PASS: MANUAL_REVIEW item rejected "
            "before external execution."
        )

        return

    raise ValidationFailure(
        "MANUAL_REVIEW item was incorrectly allowed to execute."
    )


def validate_execute_many_and_audit() -> None:
    print(
        "\n[5/5] Testing execute_many + execution audit"
    )

    successful_item = build_queue_item(
        job_id="execution-test-many-success",
        queue_status=ApplicationQueueStatus.QUEUED,
    )

    failed_item = build_queue_item(
        job_id="execution-test-many-failure",
        queue_status=ApplicationQueueStatus.QUEUED,
    )

    def fake_handler(
        item: ApplicationQueueItem,
    ) -> dict[str, Any]:
        if item.job_id == "execution-test-many-failure":
            raise RuntimeError("batch failure")

        return {
            "status": "SUBMITTED",
            "message": "Batch submission succeeded.",
            "metadata": {
                "executor": "fake",
            },
        }

    executor = ApplicationExecutor(
        handler=fake_handler,
    )

    results = executor.execute_many(
        [
            successful_item,
            failed_item,
        ]
    )

    require(
        len(results) == 2,
        f"Expected 2 execution results, got {len(results)}.",
    )

    require(
        results[0].status == "SUBMITTED",
        (
            "Expected first result SUBMITTED, "
            f"got {results[0].status!r}."
        ),
    )

    require(
        results[1].status == "FAILED",
        (
            "Expected second result FAILED, "
            f"got {results[1].status!r}."
        ),
    )

    audit_store = ApplicationExecutionAuditStore()

    audits = audit_store.record_many(
        results,
        executor="fake",
    )

    require(
        len(audits) == 2,
        f"Expected 2 audit records, got {len(audits)}.",
    )

    require(
        audit_store.summary()
        == {
            "SUBMITTED": 1,
            "FAILED": 1,
        },
        (
            "Unexpected audit summary: "
            f"{audit_store.summary()!r}."
        ),
    )

    print(
        "      PASS: batch execution and "
        "audit recording succeeded."
    )


def main() -> int:
    print("=" * 80)
    print("APPLICATION EXECUTION VALIDATION")
    print("=" * 80)

    try:
        validate_executor_without_handler()
        validate_successful_external_execution()
        validate_failed_external_execution()
        validate_non_executable_item()
        validate_execute_many_and_audit()

    except ValidationFailure as exc:
        print("")
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print(str(exc))
        return 1

    except Exception as exc:
        print("")
        print("!" * 80)
        print("UNEXPECTED VALIDATION ERROR")
        print("!" * 80)
        print(f"{type(exc).__name__}: {exc}")
        return 1

    print("")
    print("=" * 80)
    print("APPLICATION EXECUTION VALIDATION PASSED")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())