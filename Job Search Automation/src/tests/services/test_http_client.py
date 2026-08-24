from __future__ import annotations

from typing import Any

import httpx
import pytest

from job_search_automation.services.http_client import HttpClient


def make_response(
    *,
    method: str,
    url: str,
    status_code: int,
    json_data: Any = None,
    content: bytes | None = None,
) -> httpx.Response:
    request = httpx.Request(
        method,
        url,
    )

    if content is not None:
        return httpx.Response(
            status_code=status_code,
            content=content,
            request=request,
        )

    if json_data is not None:
        return httpx.Response(
            status_code=status_code,
            json=json_data,
            request=request,
        )

    return httpx.Response(
        status_code=status_code,
        request=request,
    )


def test_get_returns_json_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpClient(
        timeout=5.0,
    )

    expected = {
        "status": "ok",
        "jobs": [
            {
                "job_id": "test-001",
            }
        ],
    }

    def fake_request(
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> httpx.Response:
        assert method == "GET"
        assert url == "https://example.test/jobs"
        assert headers is None
        assert params is None
        assert json is None

        return make_response(
            method=method,
            url=url,
            status_code=200,
            json_data=expected,
        )

    monkeypatch.setattr(
        client.client,
        "request",
        fake_request,
    )

    try:
        result = client.get(
            "https://example.test/jobs",
        )

        assert result == expected

    finally:
        client.close()


def test_post_returns_json_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpClient(
        timeout=5.0,
    )

    expected = {
        "status": "accepted",
        "execution_id": "exec-001",
    }

    request_headers = {
        "Accept": "application/json",
        "Authorization": "Bearer test-token",
    }

    request_payload = {
        "event": "job_application",
        "job_id": "job-001",
    }

    def fake_request(
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> httpx.Response:
        assert method == "POST"
        assert url == "https://example.test/webhook"
        assert headers == request_headers
        assert params is None
        assert json == request_payload

        return make_response(
            method=method,
            url=url,
            status_code=200,
            json_data=expected,
        )

    monkeypatch.setattr(
        client.client,
        "request",
        fake_request,
    )

    try:
        result = client.post(
            "https://example.test/webhook",
            headers=request_headers,
            json=request_payload,
        )

        assert result == expected

    finally:
        client.close()


def test_http_500_raises_http_status_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpClient(
        timeout=5.0,
    )

    def fake_request(
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> httpx.Response:
        return make_response(
            method=method,
            url=url,
            status_code=500,
            json_data={
                "error": "server failure",
            },
        )

    monkeypatch.setattr(
        client.client,
        "request",
        fake_request,
    )

    try:
        with pytest.raises(
            httpx.HTTPStatusError,
        ):
            client.post(
                "https://example.test/webhook",
                json={
                    "event": "job_application",
                },
            )

    finally:
        client.close()


def test_http_429_raises_http_status_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpClient(
        timeout=5.0,
    )

    def fake_request(
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> httpx.Response:
        return make_response(
            method=method,
            url=url,
            status_code=429,
            json_data={
                "error": "rate limited",
            },
        )

    monkeypatch.setattr(
        client.client,
        "request",
        fake_request,
    )

    try:
        with pytest.raises(
            httpx.HTTPStatusError,
        ):
            client.post(
                "https://example.test/webhook",
                json={
                    "event": "job_application",
                },
            )

    finally:
        client.close()


def test_empty_response_returns_empty_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpClient(
        timeout=5.0,
    )

    def fake_request(
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> httpx.Response:
        return make_response(
            method=method,
            url=url,
            status_code=204,
            content=b"",
        )

    monkeypatch.setattr(
        client.client,
        "request",
        fake_request,
    )

    try:
        result = client.post(
            "https://example.test/webhook",
            json={
                "event": "job_application",
            },
        )

        assert result == {}

    finally:
        client.close()


def test_timeout_is_configured() -> None:
    client = HttpClient(
        timeout=17.5,
    )

    try:
        assert client.client.timeout.connect == 17.5
        assert client.client.timeout.read == 17.5
        assert client.client.timeout.write == 17.5
        assert client.client.timeout.pool == 17.5

    finally:
        client.close()