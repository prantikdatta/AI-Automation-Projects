from __future__ import annotations

"""
Local n8n integration validation.

Validation modes
----------------

1. Contract-only validation
- Does not require n8n.
- Validates the Python -> n8n payload contract.
- Validates headers and configuration.
- Validates response normalisation.

2. Live local n8n validation
- Requires a locally running n8n instance.
- Sends one deterministic test application payload.
- Validates the HTTP response.
- Does NOT submit a real job application.

Environment variables
---------------------

Required for live validation:

    N8N_WEBHOOK_URL

Optional:

    N8N_WEBHOOK_TOKEN
    N8N_BASIC_AUTH_USER
    N8N_BASIC_AUTH_PASSWORD
    N8N_WEBHOOK_TIMEOUT

Example:

    N8N_WEBHOOK_URL=http://127.0.0.1:5678/webhook/job-application

Usage
-----

Contract validation:

    python scripts/validation/validate_local_n8n.py

Live validation:

    python scripts/validation/validate_local_n8n.py --live

The live webhook must point to a SAFE n8n workflow that only acknowledges
the request. It must not submit an actual application.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Repository import setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.queue import (  # noqa: E402
    ApplicationQueueItem,
    ApplicationQueueStatus,
)
from job_search_automation.application.n8n_handler import (  # noqa: E402
    N8nApplicationHandler,
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class ValidationFailure(AssertionError):
    """Raised when a local n8n integration invariant fails."""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise ValidationFailure(message)


def build_test_queue_item() -> ApplicationQueueItem:
    """
    Build a deterministic production-contract queue item.

    This item is used only for integration validation.

    READY is the canonical application queue state used by the
    current application layer.
    """

    return ApplicationQueueItem(
        job_id="n8n-local-validation-001",
        title="Senior Data Analyst",
        company="N8N Validation Company",
        location="Mumbai",
        job_url="https://example.com/n8n-local-validation-001",
        provider="validation",
        source="validation",
        searched_role="Data Analyst",
        overall_score=82.5,
        score=82.5,
        selection_bucket="A - Apply Now",
        readiness_decision="READY",
        queue_status=ApplicationQueueStatus.READY,
        decision=ApplicationQueueStatus.READY,
        status=ApplicationQueueStatus.READY,
        eligible=True,
        reason="Deterministic n8n integration validation item.",
        resume_tailoring_required=False,
        notes=[
            "Local n8n integration validation only.",
        ],
        recommended_actions=[
            "Do not submit a real application.",
        ],
        application_url=None,
    )


# ---------------------------------------------------------------------------
# Payload validation
# ---------------------------------------------------------------------------


def validate_payload_contract(
    handler: N8nApplicationHandler,
    item: ApplicationQueueItem,
) -> dict[str, Any]:
    print(
        "\n[1/5] Validating Python -> n8n payload contract"
    )

    payload = handler.build_payload(item)

    require(
        isinstance(payload, dict),
        "Payload must be a dictionary.",
    )

    require(
        payload.get("event") == "job_application",
        "Payload event is incorrect.",
    )

    require(
        payload.get("version") == "1.0",
        "Payload version is incorrect.",
    )

    job = payload.get("job")

    require(
        isinstance(job, dict),
        "Payload job section is missing.",
    )

    application = payload.get("application")

    require(
        isinstance(application, dict),
        "Payload application section is missing.",
    )

    require(
        job.get("job_id")
        == "n8n-local-validation-001",
        "Payload job_id is incorrect.",
    )

    require(
        job.get("title")
        == "Senior Data Analyst",
        "Payload title is incorrect.",
    )

    require(
        job.get("company")
        == "N8N Validation Company",
        "Payload company is incorrect.",
    )

    require(
        job.get("location")
        == "Mumbai",
        "Payload location is incorrect.",
    )

    require(
        job.get("job_url")
        == "https://example.com/n8n-local-validation-001",
        "Payload job_url is incorrect.",
    )

    require(
        job.get("provider") == "validation",
        "Payload provider is incorrect.",
    )

    require(
        application.get("readiness_decision")
        == "READY",
        "Payload readiness_decision is incorrect.",
    )

    require(
        application.get("queue_status")
        == "READY",
        "Payload queue_status is incorrect.",
    )

    require(
        application.get("decision")
        == "READY",
        "Payload decision is incorrect.",
    )

    require(
        application.get("status")
        == "READY",
        "Payload status is incorrect.",
    )

    require(
        application.get("eligible") is True,
        "Payload eligible flag is incorrect.",
    )

    require(
        application.get("resume_tailoring_required")
        is False,
        "Payload resume_tailoring_required is incorrect.",
    )

    require(
        isinstance(
            application.get("notes"),
            list,
        ),
        "Payload notes must be a list.",
    )

    require(
        isinstance(
            application.get("recommended_actions"),
            list,
        ),
        "Payload recommended_actions must be a list.",
    )

    print(
        "      PASS: payload contract is valid."
    )

    return payload


# ---------------------------------------------------------------------------
# Header validation
# ---------------------------------------------------------------------------


def validate_headers(
    handler: N8nApplicationHandler,
) -> None:
    print(
        "\n[2/5] Validating HTTP headers"
    )

    headers = handler._build_headers()

    require(
        headers.get("Content-Type")
        == "application/json",
        "Content-Type header is incorrect.",
    )

    require(
        headers.get("Accept")
        == "application/json",
        "Accept header is incorrect.",
    )

    print(
        "      PASS: HTTP headers are valid."
    )


# ---------------------------------------------------------------------------
# Bearer authentication validation
# ---------------------------------------------------------------------------


def validate_bearer_auth() -> None:
    print(
        "\n[3/5] Validating optional Bearer authentication"
    )

    handler = N8nApplicationHandler(
        webhook_url=(
            "http://127.0.0.1:5678/"
            "webhook/job-application"
        ),
        webhook_token="test-token",
    )

    headers = handler._build_headers()

    require(
        headers.get("Authorization")
        == "Bearer test-token",
        "Bearer Authorization header is incorrect.",
    )

    print(
        "      PASS: Bearer authentication is supported."
    )


# ---------------------------------------------------------------------------
# Basic authentication validation
# ---------------------------------------------------------------------------


def validate_basic_auth() -> None:
    print(
        "\n[4/5] Validating optional Basic authentication"
    )

    handler = N8nApplicationHandler(
        webhook_url=(
            "http://127.0.0.1:5678/"
            "webhook/job-application"
        ),
        basic_auth_user="test-user",
        basic_auth_password="test-password",
    )

    headers = handler._build_headers()

    require(
        headers.get("Authorization")
        == "Basic dGVzdC11c2VyOnRlc3QtcGFzc3dvcmQ=",
        "Basic Authorization header is incorrect.",
    )

    print(
        "      PASS: Basic authentication is supported."
    )


# ---------------------------------------------------------------------------
# Response normalisation
# ---------------------------------------------------------------------------


def validate_response_normalisation(
    item: ApplicationQueueItem,
) -> None:
    print(
        "\n[5/5] Validating n8n response normalisation"
    )

    response = {
        "status": "SUBMITTED",
        "message": "Validation workflow completed.",
        "metadata": {
            "workflow": "local-n8n-validation",
            "test": True,
        },
    }

    result = N8nApplicationHandler._normalise_response(
        response,
        item,
    )

    require(
        isinstance(result, dict),
        "Normalised response must be a dictionary.",
    )

    require(
        result.get("status") == "SUBMITTED",
        "Normalised response status is incorrect.",
    )

    require(
        result.get("message")
        == "Validation workflow completed.",
        "Normalised response message is incorrect.",
    )

    metadata = result.get("metadata")

    require(
        isinstance(metadata, dict),
        "Normalised metadata must be a dictionary.",
    )

    require(
        metadata.get("workflow")
        == "local-n8n-validation",
        "n8n metadata was not preserved.",
    )

    require(
        metadata.get("test") is True,
        "n8n test metadata was not preserved.",
    )

    require(
        metadata.get("executor") == "n8n",
        "Default n8n executor metadata is missing.",
    )

    require(
        metadata.get("webhook")
        == "n8n:n8n-local-validation-001",
        "Safe webhook marker is incorrect.",
    )

    print(
        "      PASS: n8n response normalisation is valid."
    )


# ---------------------------------------------------------------------------
# Live local n8n validation
# ---------------------------------------------------------------------------


class LiveHttpClient:
    """
    Minimal HTTP client adapter used only by the live validator.

    The production N8nApplicationHandler normally uses the project's
    HttpClient. This adapter allows the validation script to exercise the
    actual webhook without introducing another production dependency.
    """

    def __init__(
        self,
        timeout: float,
    ) -> None:
        import httpx

        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
        )

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._client.post(
            url,
            headers=headers,
            json=json,
        )

        response.raise_for_status()

        if not response.content:
            return {}

        data = response.json()

        require(
            isinstance(data, dict),
            (
                "Local n8n webhook must return "
                "a JSON object."
            ),
        )

        return data

    def close(self) -> None:
        self._client.close()


def validate_live_n8n(
    item: ApplicationQueueItem,
) -> None:
    print()
    print("=" * 80)
    print("LIVE LOCAL N8N WEBHOOK VALIDATION")
    print("=" * 80)

    webhook_url = os.getenv(
        "N8N_WEBHOOK_URL",
        "",
    ).strip()

    require(
        webhook_url,
        (
            "N8N_WEBHOOK_URL is not configured. "
            "Set it before using --live."
        ),
    )

    timeout_raw = os.getenv(
        "N8N_WEBHOOK_TIMEOUT",
        "30",
    ).strip()

    try:
        timeout = float(timeout_raw)
    except ValueError as exc:
        raise ValidationFailure(
            "N8N_WEBHOOK_TIMEOUT must be numeric."
        ) from exc

    print()
    print(
        f"Webhook: {webhook_url}"
    )

    print(
        "WARNING: This sends a validation payload only."
    )

    print(
        "No real application submission should be connected "
        "to this webhook."
    )

    http_client = LiveHttpClient(
        timeout=timeout,
    )

    try:
        handler = N8nApplicationHandler(
            webhook_url=webhook_url,
            webhook_token=os.getenv(
                "N8N_WEBHOOK_TOKEN",
                "",
            ).strip(),
            basic_auth_user=os.getenv(
                "N8N_BASIC_AUTH_USER",
                "",
            ).strip(),
            basic_auth_password=os.getenv(
                "N8N_BASIC_AUTH_PASSWORD",
                "",
            ),
            timeout=timeout,
            http_client=http_client,  # type: ignore[arg-type]
        )

        payload = handler.build_payload(
            item
        )

        response = http_client.post(
            webhook_url,
            headers=handler._build_headers(),
            json=payload,
        )

        result = handler._normalise_response(
            response,
            item,
        )

        require(
            isinstance(result, dict),
            "n8n returned an invalid handler result.",
        )

        require(
            bool(
                str(
                    result.get(
                        "status",
                        "",
                    )
                ).strip()
            ),
            "n8n response does not contain a status.",
        )

        print()
        print(
            "n8n response:"
        )

        print(
            f"  status  : {result['status']}"
        )

        print(
            f"  message : {result['message']}"
        )

        print(
            f"  metadata: {result['metadata']}"
        )

        print()
        print(
            "PASS: local n8n webhook responded "
            "with a valid application-execution contract."
        )

    except Exception as exc:
        raise ValidationFailure(
            (
                "Local n8n webhook validation failed: "
                f"{type(exc).__name__}: {exc}"
            )
        ) from exc

    finally:
        http_client.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Python -> local n8n "
            "application execution boundary."
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Send a deterministic validation payload "
            "to the configured local n8n webhook."
        ),
    )

    args = parser.parse_args()

    print("=" * 80)
    print("LOCAL N8N APPLICATION HANDLER VALIDATION")
    print("=" * 80)

    print(
        "Contract validation does not require n8n."
    )

    item = build_test_queue_item()

    try:
        handler = N8nApplicationHandler(
            webhook_url=(
                "http://127.0.0.1:5678/"
                "webhook/job-application"
            )
        )

        validate_payload_contract(
            handler,
            item,
        )

        validate_headers(
            handler,
        )

        validate_bearer_auth()

        validate_basic_auth()

        validate_response_normalisation(
            item,
        )

        if args.live:
            validate_live_n8n(
                item,
            )

    except ValidationFailure as exc:
        print()
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print(str(exc))
        return 1

    except Exception as exc:
        print()
        print("!" * 80)
        print("UNEXPECTED VALIDATION ERROR")
        print("!" * 80)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1

    print()
    print("=" * 80)
    print("LOCAL N8N APPLICATION HANDLER VALIDATION PASSED")
    print("=" * 80)

    if args.live:
        print(
            "Live local n8n webhook validation completed."
        )
    else:
        print(
            "Contract validation completed."
        )
        print(
            "Run with --live after the local n8n webhook "
            "workflow is configured."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())