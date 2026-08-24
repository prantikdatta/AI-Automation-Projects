from __future__ import annotations

from datetime import datetime, timezone

import pytest

from job_search_automation.application.n8n_handler import (
    N8nApplicationHandler,
)
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)


class FakeHttpClient:
    def __init__(self, response=None):
        self.response = response
        self.calls = []

    def post(self, url, headers=None, json=None):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
            }
        )
        return self.response


def make_item() -> ApplicationQueueItem:
    return ApplicationQueueItem(
        job_id="stripe|data analyst|mumbai|https://example.com/job",
        title="Data Analyst",
        company="Stripe",
        location="Mumbai",
        job_url="https://example.com/job",
        score=87.5,
        decision="READY",
        searched_role="Data Analyst",
        source="test",
        resume_match_score=91.0,
        created_at=datetime(
            2026,
            8,
            13,
            10,
            30,
            tzinfo=timezone.utc,
        ).isoformat(),
        status="READY",
        queue_status=ApplicationQueueStatus.QUEUED,
    )


def test_build_payload_contains_stable_contract():
    handler = N8nApplicationHandler(
        webhook_url="http://127.0.0.1:5678/webhook/job-application"
    )

    payload = handler.build_payload(make_item())

    assert payload["event"] == "job_application"
    assert payload["version"] == "1.0"

    assert payload["job"]["job_id"] == (
        "stripe|data analyst|mumbai|https://example.com/job"
    )
    assert payload["job"]["title"] == "Data Analyst"
    assert payload["job"]["company"] == "Stripe"
    assert payload["job"]["location"] == "Mumbai"
    assert payload["job"]["job_url"] == "https://example.com/job"

    assert payload["application"]["queue_status"] == "READY"


def test_build_headers_without_authentication():
    handler = N8nApplicationHandler(
        webhook_url="http://127.0.0.1:5678/webhook/job-application"
    )

    headers = handler._build_headers()

    assert headers == {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def test_build_headers_with_bearer_token():
    handler = N8nApplicationHandler(
        webhook_url="http://127.0.0.1:5678/webhook/job-application",
        webhook_token="test-token",
    )

    headers = handler._build_headers()

    assert headers["Authorization"] == "Bearer test-token"


def test_handler_posts_payload_to_webhook():
    fake_client = FakeHttpClient(
        response={
            "status": "SUBMITTED",
            "message": "Application submitted.",
            "metadata": {
                "execution_id": "123",
            },
        }
    )

    handler = N8nApplicationHandler(
        webhook_url="http://127.0.0.1:5678/webhook/job-application",
        http_client=fake_client,
    )

    result = handler(make_item())

    assert len(fake_client.calls) == 1

    call = fake_client.calls[0]

    assert call["url"] == (
        "http://127.0.0.1:5678/webhook/job-application"
    )

    assert call["headers"]["Content-Type"] == "application/json"

    assert call["json"]["event"] == "job_application"

    assert result["status"] == "SUBMITTED"
    assert result["message"] == "Application submitted."
    assert result["metadata"]["execution_id"] == "123"
    assert result["metadata"]["executor"] == "n8n"


def test_handler_requires_webhook_url():
    handler = N8nApplicationHandler(
        webhook_url="",
    )

    with pytest.raises(
        RuntimeError,
        match="N8N_WEBHOOK_URL is not configured",
    ):
        handler(make_item())


def test_handler_rejects_invalid_webhook_scheme():
    handler = N8nApplicationHandler(
        webhook_url="ftp://127.0.0.1:5678/webhook/job-application"
    )

    with pytest.raises(
        RuntimeError,
        match="must use http:// or https://",
    ):
        handler(make_item())


def test_handler_rejects_non_dict_response():
    with pytest.raises(
        TypeError,
        match="n8n webhook response must be a JSON object",
    ):
        N8nApplicationHandler._normalise_response(
            response="invalid",
            item=make_item(),
        )