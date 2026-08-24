from __future__ import annotations

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
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)


def build_item() -> ApplicationQueueItem:
    return ApplicationQueueItem(
        job_id="application-failure-validation-001",
        title="Senior Data Analyst",
        company="Failure Validation Company",
        location="Mumbai",
        job_url="https://example.com/failure-validation-001",
        provider="validation",
        source="validation",
        searched_role="Senior Data Analyst",
        overall_score=90.0,
        score=90.0,
        selection_bucket="A - Apply Now",
        readiness_decision=ApplicationQueueStatus.READY,
        queue_status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Synthetic failure validation.",
        resume_match_score=90.0,
        notes=["FAILURE_VALIDATION_ONLY"],
        application_url=None,
    )


def failing_handler(
    item: ApplicationQueueItem,
) -> dict[str, Any]:
    raise RuntimeError(
        "Synthetic external application failure."
    )


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    print("=" * 80)
    print("APPLICATION EXECUTION FAILURE VALIDATION")
    print("=" * 80)
    print()

    item = build_item()

    try:
        print("[1/5] Validating executable queue item")

        if item.queue_status != ApplicationQueueStatus.QUEUED:
            fail(
                "Synthetic item must be executable."
            )

        print(
            "      PASS: queue item is executable."
        )
        print()

        print("[2/5] Creating ApplicationExecutor")

        executor = ApplicationExecutor(
            handler=failing_handler,
        )

        print(
            "      PASS: executor created."
        )
        print()

        print(
            "[3/5] Validating external execution failure"
        )

        try:
            executor.execute(item)

        except ApplicationExecutionError as exc:
            if "Synthetic external application failure" not in str(exc):
                fail(
                    "ApplicationExecutionError did not preserve "
                    "the underlying failure."
                )

            print(
                "      PASS: external failure converted to "
                "ApplicationExecutionError."
            )

        else:
            fail(
                "Expected ApplicationExecutionError."
            )

        print()

        print(
            "[4/5] Validating execute_many failure isolation"
        )

        results = executor.execute_many(
            [item]
        )

        if len(results) != 1:
            fail(
                "execute_many() returned an unexpected result count."
            )

        result = results[0]

        if result.job_id != item.job_id:
            fail(
                "Failed execution result has incorrect job_id."
            )

        if result.status != "FAILED":
            fail(
                f"Expected FAILED, got {result.status!r}."
            )

        if not result.message:
            fail(
                "Failed execution result has no message."
            )

        print(
            "      PASS: execute_many() converted failure "
            "to FAILED result."
        )
        print()

        print(
            "[5/5] Validating failure audit transition"
        )

        audit = ApplicationExecutionAudit(
            job_id=item.job_id,
        )

        audit.mark_ready(
            message="Synthetic application execution ready.",
            metadata={
                "executor": "validation",
                "validation": True,
            },
        )

        audit.mark_failed(
            message=result.message,
            metadata={
                "executor": "validation",
                "validation": True,
                "error_type": "ApplicationExecutionError",
            },
        )

        if audit.status != ApplicationExecutionAudit.FAILED:
            fail(
                f"Expected FAILED audit status, "
                f"got {audit.status!r}."
            )

        payload = audit.to_dict()

        if payload["job_id"] != item.job_id:
            fail(
                "Audit job_id changed during serialization."
            )

        if payload["status"] != "FAILED":
            fail(
                "Audit status serialization is incorrect."
            )

        if payload["metadata"].get("error_type") != (
            "ApplicationExecutionError"
        ):
            fail(
                "Audit error metadata was not preserved."
            )

        print(
            "      PASS: execution audit reached FAILED."
        )
        print()

        print("=" * 80)
        print(
            "APPLICATION EXECUTION FAILURE VALIDATION PASSED"
        )
        print("=" * 80)
        print()
        print(f"job_id : {result.job_id}")
        print(f"status : {result.status}")
        print(f"audit  : {audit.status}")

        return 0

    except Exception as exc:
        print()
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())