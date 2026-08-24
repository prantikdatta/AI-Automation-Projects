from __future__ import annotations

from fastapi.testclient import TestClient

from job_search_automation.app import app
from job_search_automation.models.response import SearchResponse


def test_jobs_search_endpoint_exists() -> None:
    route_paths = {
        route.path
        for route in app.routes
    }

    assert "/jobs/search" in route_paths


def test_jobs_search_serializes_search_response(
    monkeypatch,
) -> None:
    class FakePipeline:
        def run(self) -> SearchResponse:
            return SearchResponse(
                success=True,
                jobs=[],
                total_found=0,
                total_returned=0,
            )

    monkeypatch.setattr(
        "job_search_automation.api.jobs.SearchPipeline",
        FakePipeline,
    )

    client = TestClient(app)

    response = client.post("/jobs/search")

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["jobs"] == []
    assert body["total_found"] == 0
    assert body["total_returned"] == 0