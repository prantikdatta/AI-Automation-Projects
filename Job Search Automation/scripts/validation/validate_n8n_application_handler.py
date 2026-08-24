from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


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
        job_id="n8n-handler-validation-001",
        title="Senior Data Analyst",
        company="Validation Company",
        location="Mumbai",
        job_url="https://example.com/job-001",
        provider="validation",
        source="validation",
        searched_role="Senior Data Analyst",
        overall_score=90.0,
        score=90.0,
        selection_bucket="A - Apply Now",
        readiness_decision=ApplicationQueueStatus.READY,
        queue_status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Synthetic handler validation.",
        resume_match_score=90.0,
        notes=["HANDLER_VALIDATION_ONLY"],
        application_url=None,
    )


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    print("=" * 80)
    print("N8N APPLICATION HANDLER CONTRACT VALIDATION")
    print("=" * 80)
    print()

    item = build_item()

    fake_client = FakeHttpClient(
        {
            "status": "SUBMITTED",
            "message": "n8n validation completed.",
            "metadata": {
                "validation": True,
            },
        }
    )

    handler = N8nApplicationHandler(
        webhook_url="http://127.0.0.1:5678/webhook-test/job-application",
        http_client=fake_client,
    )

    try:
        print("[1/5] Validating handler configuration")

        if not handler.webhook_url:
            fail("Webhook URL was not configured.")

        if handler.timeout <= 0:
            fail("Handler timeout must be greater than zero.")

        print("      PASS: handler configuration is valid.")
        print()

        print("[2/5] Validating canonical payload")

        payload = handler.build_payload(item)

        if payload["event"] != "job_application":
            fail("Payload event is incorrect.")

        if payload["version"] != "1.0":
            fail("Payload version is incorrect.")

        if payload["job"]["job_id"] != item.job_id:
            fail("Payload job_id is incorrect.")

        if payload["job"]["title"] != item.title:
            fail("Payload title is incorrect.")

        if payload["job"]["company"] != item.company:
            fail("Payload company is incorrect.")

        if payload["application"]["queue_status"] != "READY":
            fail("Payload queue_status is incorrect.")

        if payload["application"]["eligible"] is not True:
            fail("Payload eligibility is incorrect.")

        print("      PASS: canonical payload is valid.")
        print()

        print("[3/5] Validating HTTP POST contract")

        result = handler(item)

        if len(fake_client.calls) != 1:
            fail(
                "Expected exactly one HTTP POST call."
            )

        call = fake_client.calls[0]

        if call["url"] != handler.webhook_url:
            fail("Webhook URL was not forwarded correctly.")

        if call["headers"]["Content-Type"] != "application/json":
            fail("Content-Type header is incorrect.")

        if call["headers"]["Accept"] != "application/json":
            fail("Accept header is incorrect.")

        if call["json"] != payload:
            fail("POST payload differs from canonical payload.")

        print("      PASS: HTTP POST contract is valid.")
        print()

        print("[4/5] Validating response normalization")

        if result["status"] != "SUBMITTED":
            fail(
                f"Expected SUBMITTED, got {result['status']!r}."
            )

        if result["message"] != "n8n validation completed.":
            fail("Response message was not preserved.")

        if result["metadata"]["executor"] != "n8n":
            fail("Executor metadata is missing.")

        if result["metadata"]["validation"] is not True:
            fail("Validation metadata was not preserved.")

        if result["metadata"]["webhook"] != (
            "n8n:n8n-handler-validation-001"
        ):
            fail("Webhook execution marker is incorrect.")

        print("      PASS: response normalization is valid.")
        print()

        print("[5/5] Validating authentication header generation")

        token_handler = N8nApplicationHandler(
            webhook_url="http://127.0.0.1:5678/webhook-test/job-application",
            webhook_token="validation-token",
            http_client=fake_client,
        )

        token_headers = token_handler._build_headers()

        if token_headers.get("Authorization") != (
            "Bearer validation-token"
        ):
            fail("Bearer authorization header is incorrect.")

        print("      PASS: authentication header contract is valid.")
        print()

        print("=" * 80)
        print("N8N APPLICATION HANDLER CONTRACT VALIDATION PASSED")
        print("=" * 80)

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