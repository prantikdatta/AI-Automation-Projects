from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

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
    QueueStatus,
)


def build_validation_item() -> ApplicationQueueItem:
    """
    Build a synthetic queue item for local n8n validation only.

    This item must never be connected to a real application.
    """

    return ApplicationQueueItem(
        job_id="n8n-validation-job-001",
        title="N8n Validation Application",
        company="Local Validation Company",
        location="Mumbai",
        job_url="https://example.com/n8n-validation-job-001",
        provider="validation",
        source="validation",
        searched_role="Data Analyst",
        overall_score=95.0,
        score=95.0,
        selection_bucket="A - Apply Now",
        readiness_decision=QueueStatus.READY,
        queue_status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Synthetic local n8n validation item.",
        resume_match_score=95.0,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=["LOCAL_N8N_VALIDATION_ONLY"],
        application_url=None,
    )


def validate_result(
    result: Any,
    audit: ApplicationExecutionAudit,
) -> None:

    if result.job_id != "n8n-validation-job-001":
        raise AssertionError(
            f"Unexpected job_id: {result.job_id!r}"
        )

    if result.status != "SUBMITTED":
        raise AssertionError(
            f"Expected SUBMITTED status, got {result.status!r}."
        )

    if not result.message:
        raise AssertionError(
            "n8n execution returned an empty message."
        )

    if result.metadata.get("executor") != "n8n":
        raise AssertionError(
            "Expected execution metadata executor='n8n'."
        )

    if not result.metadata.get("webhook"):
        raise AssertionError(
            "Expected n8n webhook execution marker."
        )

    if audit.status != ApplicationExecutionAudit.SUBMITTED:
        raise AssertionError(
            (
                "Expected audit status SUBMITTED, "
                f"got {audit.status!r}."
            )
        )

    if audit.job_id != result.job_id:
        raise AssertionError(
            "Audit job_id does not match execution result."
        )


def main() -> int:

    print("=" * 80)
    print("APPLICATION EXECUTION -> LOCAL N8N VALIDATION")
    print("=" * 80)
    print()

    print(
        "WARNING: This validation uses a synthetic payload only."
    )
    print(
        "No real application submission should be connected "
        "to this webhook."
    )
    print()

    try:

        # ----------------------------------------------------------
        # 1. Build synthetic queue item
        # ----------------------------------------------------------

        print(
            "[1/4] Building synthetic ApplicationQueueItem"
        )

        item = build_validation_item()

        if item.queue_status != ApplicationQueueStatus.QUEUED:
            raise AssertionError(
                (
                    "Synthetic validation item must have "
                    "queue_status=QUEUED."
                )
            )

        if not item.eligible:
            raise AssertionError(
                "Synthetic validation item must be eligible."
            )

        print(
            "      PASS: synthetic queue item is executable."
        )
        print()

        # ----------------------------------------------------------
        # 2. Create n8n handler
        # ----------------------------------------------------------

        print(
            "[2/4] Creating N8nApplicationHandler"
        )

        handler = N8nApplicationHandler()

        print(
            "      PASS: n8n application handler created."
        )
        print()

        # ----------------------------------------------------------
        # 3. Execute through production executor
        # ----------------------------------------------------------

        print(
            "[3/4] Executing through ApplicationExecutor"
        )

        executor = ApplicationExecutor(
            handler=handler,
        )

        audit = ApplicationExecutionAudit(
            job_id=item.job_id,
        )

        audit.mark_ready(
            message=(
                "Application execution ready "
                "for local n8n validation."
            ),
            metadata={
                "executor": "n8n",
                "validation": True,
            },
        )

        try:

            result = executor.execute(item)

        except ApplicationExecutionError as exc:

            audit.mark_failed(
                message=str(exc),
                metadata={
                    "executor": "n8n",
                    "validation": True,
                    "error_type": type(exc).__name__,
                },
            )

            raise

        audit.mark_submitted(
            message=result.message,
            metadata=result.metadata,
        )

        print(
            "      PASS: ApplicationExecutor "
            "received n8n response."
        )
        print()

        # ----------------------------------------------------------
        # 4. Validate execution + audit contracts
        # ----------------------------------------------------------

        print(
            "[4/4] Validating execution + audit contract"
        )

        validate_result(
            result,
            audit,
        )

        print(
            "      PASS: execution result is valid."
        )

        print(
            "      PASS: execution audit reached SUBMITTED."
        )

        print()

        print("=" * 80)
        print(
            "APPLICATION EXECUTION -> LOCAL N8N "
            "VALIDATION PASSED"
        )
        print("=" * 80)
        print()

        print(f"status  : {result.status}")
        print(f"message : {result.message}")
        print(f"metadata: {result.metadata}")
        print(f"audit   : {audit.status}")

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