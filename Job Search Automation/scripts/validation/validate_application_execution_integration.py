from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.execution import (
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


class FakeHttpClient:
    def __init__(
        self,
        response: dict[str, Any],
    ) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
            }
        )
        return self.response


def build_item() -> ApplicationQueueItem:
    return ApplicationQueueItem(
        job_id="application-integration-validation-001",
        title="Senior Data Analyst",
        company="Integration Validation Company",
        location="Mumbai",
        job_url="https://example.com/application-validation-001",
        provider="validation",
        source="validation",
        searched_role="Senior Data Analyst",
        overall_score=92.0,
        score=92.0,
        selection_bucket="A - Apply Now",
        readiness_decision=ApplicationQueueStatus.READY,
        queue_status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Synthetic end-to-end application validation.",
        resume_match_score=92.0,
        notes=["INTEGRATION_VALIDATION_ONLY"],
        application_url=None,
    )


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    print("=" * 80)
    print("APPLICATION EXECUTION INTEGRATION VALIDATION")
    print("=" * 80)
    print()

    item = build_item()

    fake_client = FakeHttpClient(
        {
            "status": "SUBMITTED",
            "message": "n8n application workflow completed.",
            "metadata": {
                "validation": True,
            },
        }
    )

    handler = N8nApplicationHandler(
        webhook_url=(
            "http://127.0.0.1:5678/"
            "webhook-test/job-application"
        ),
        http_client=fake_client,
    )

    try:
        print("[1/6] Validating executable queue item")

        if item.queue_status != ApplicationQueueStatus.QUEUED:
            fail(
                "Queue item must have queue_status=QUEUED."
            )

        if not item.eligible:
            fail(
                "Queue item must be eligible."
            )

        print(
            "      PASS: queue item is executable."
        )
        print()

        print(
            "[2/6] Creating N8nApplicationHandler"
        )

        if not handler.webhook_url:
            fail(
                "n8n webhook URL is missing."
            )

        print(
            "      PASS: n8n handler created."
        )
        print()

        print(
            "[3/6] Creating ApplicationExecutor"
        )

        executor = ApplicationExecutor(
            handler=handler,
        )

        print(
            "      PASS: ApplicationExecutor created."
        )
        print()

        print(
            "[4/6] Executing queue item through "
            "ApplicationExecutor -> N8nApplicationHandler"
        )

        result = executor.execute(item)

        if result.job_id != item.job_id:
            fail(
                "Execution result job_id does not match queue item."
            )

        if result.status != "SUBMITTED":
            fail(
                f"Expected SUBMITTED, got {result.status!r}."
            )

        if not result.message:
            fail(
                "Execution result message is empty."
            )

        if result.metadata.get("executor") != "n8n":
            fail(
                "Execution metadata executor must be 'n8n'."
            )

        print(
            "      PASS: ApplicationExecutor execution succeeded."
        )
        print(
            f"      status : {result.status}"
        )
        print(
            f"      message: {result.message}"
        )
        print(
            f"      metadata: {result.metadata}"
        )
        print()

        print(
            "[5/6] Validating HTTP boundary"
        )

        if len(fake_client.calls) != 1:
            fail(
                "Expected exactly one HTTP POST."
            )

        call = fake_client.calls[0]

        if call["url"] != handler.webhook_url:
            fail(
                "Incorrect n8n webhook URL."
            )

        payload = call["json"]

        if payload["event"] != "job_application":
            fail(
                "Incorrect n8n event."
            )

        if payload["job"]["job_id"] != item.job_id:
            fail(
                "n8n payload job_id mismatch."
            )

        if payload["application"]["eligible"] is not True:
            fail(
                "n8n payload eligibility mismatch."
            )

        print(
            "      PASS: HTTP boundary contract is valid."
        )
        print()

        print(
            "[6/6] Validating ApplicationExecutionAudit"
        )

        audit = ApplicationExecutionAudit(
            job_id=item.job_id,
        )

        audit.mark_ready(
            message="Application execution ready.",
            metadata={
                "executor": "n8n",
                "validation": True,
            },
        )

        audit.mark_submitted(
            message=result.message,
            metadata=result.metadata,
        )

        if audit.status != ApplicationExecutionAudit.SUBMITTED:
            fail(
                f"Expected audit SUBMITTED, got {audit.status!r}."
            )

        audit_payload = audit.to_dict()

        if audit_payload["job_id"] != item.job_id:
            fail(
                "Audit job_id mismatch."
            )

        if audit_payload["status"] != "SUBMITTED":
            fail(
                "Audit status serialization mismatch."
            )

        if audit_payload["metadata"].get("executor") != "n8n":
            fail(
                "Audit executor metadata mismatch."
            )

        print(
            "      PASS: execution audit reached SUBMITTED."
        )
        print()

        print("=" * 80)
        print(
            "APPLICATION EXECUTION INTEGRATION VALIDATION PASSED"
        )
        print("=" * 80)
        print()
        print(f"job_id  : {result.job_id}")
        print(f"status  : {result.status}")
        print(f"message : {result.message}")
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