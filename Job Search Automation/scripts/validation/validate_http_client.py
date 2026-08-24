from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.services.http_client import HttpClient


SEPARATOR = "=" * 80


class MockResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: dict[str, Any] | None = None,
        content: bytes = b"{}",
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request(
                    "GET",
                    "http://validation.local",
                ),
                response=httpx.Response(
                    self.status_code,
                ),
            )


class MockHttpxClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: Any = None,
        params: Any = None,
        json: Any = None,
    ) -> MockResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "json": json,
            }
        )

        return MockResponse(
            status_code=200,
            payload={
                "status": "ok",
                "validation": True,
            },
        )

    def close(self) -> None:
        pass


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    print(SEPARATOR)
    print("HTTP CLIENT CONTRACT VALIDATION")
    print(SEPARATOR)
    print()

    client = HttpClient(timeout=5.0)

    mock_client = MockHttpxClient()
    client.client = mock_client

    try:
        print("[1/5] Validating HttpClient construction")

        if client.client is None:
            fail("HttpClient.client was not initialized.")

        print("      PASS: HttpClient constructed.")
        print()

        print("[2/5] Validating GET contract")

        get_result = client.get(
            "http://validation.local/jobs",
            headers={
                "Accept": "application/json",
            },
            params={
                "q": "data analyst",
            },
        )

        if get_result != {
            "status": "ok",
            "validation": True,
        }:
            fail(
                "Unexpected GET response: "
                f"{get_result!r}"
            )

        if len(mock_client.calls) != 1:
            fail(
                "Expected exactly one HTTP call after GET."
            )

        get_call = mock_client.calls[0]

        if get_call["method"] != "GET":
            fail(
                f"Expected GET method, got {get_call['method']!r}."
            )

        if get_call["params"] != {
            "q": "data analyst",
        }:
            fail(
                "GET parameters were not forwarded correctly."
            )

        print("      PASS: GET contract is valid.")
        print()

        print("[3/5] Validating POST contract")

        post_payload = {
            "event": "job_application",
            "version": "1.0",
        }

        post_result = client.post(
            "http://validation.local/webhook",
            headers={
                "Content-Type": "application/json",
            },
            json=post_payload,
        )

        if post_result != {
            "status": "ok",
            "validation": True,
        }:
            fail(
                "Unexpected POST response: "
                f"{post_result!r}"
            )

        if len(mock_client.calls) != 2:
            fail(
                "Expected exactly two HTTP calls after POST."
            )

        post_call = mock_client.calls[1]

        if post_call["method"] != "POST":
            fail(
                f"Expected POST method, got {post_call['method']!r}."
            )

        if post_call["json"] != post_payload:
            fail(
                "POST JSON payload was not forwarded correctly."
            )

        print("      PASS: POST contract is valid.")
        print()

        print("[4/5] Validating HTTP error propagation")

        error_client = MockHttpxClient()

        def error_request(
            *,
            method: str,
            url: str,
            headers: Any = None,
            params: Any = None,
            json: Any = None,
        ) -> MockResponse:
            return MockResponse(
                status_code=404,
                payload={
                    "error": "not_found",
                },
                content=b'{"error":"not_found"}',
            )

        error_client.request = error_request  # type: ignore[method-assign]

        error_http_client = HttpClient(timeout=5.0)
        error_http_client.client = error_client

        try:
            error_http_client.get(
                "http://validation.local/missing"
            )

        except httpx.HTTPStatusError:
            print(
                "      PASS: HTTP error is propagated correctly."
            )

        else:
            fail(
                "Expected httpx.HTTPStatusError for HTTP 404."
            )

        finally:
            error_http_client.close()

        print()

        print("[5/5] Validating resource cleanup")

        client.close()

        print("      PASS: HttpClient.close() completed.")
        print()

        print(SEPARATOR)
        print("HTTP CLIENT CONTRACT VALIDATION PASSED")
        print(SEPARATOR)

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

    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())