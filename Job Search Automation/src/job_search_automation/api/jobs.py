from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import APIRouter, HTTPException

from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


def _serialize(value: Any) -> Any:
    """
    Serialize existing production response/model objects
    without changing the production models.
    """

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, list):
        return [_serialize(item) for item in value]

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    return value


@router.post(
    "/search",
    response_model=None,
)
def search_jobs() -> dict[str, Any]:
    """
    Execute the existing production SearchPipeline.

    SearchPipeline remains the single production
    orchestration boundary.
    """

    try:
        pipeline = SearchPipeline()
        response = pipeline.run()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Job search pipeline failed: {exc}",
        ) from exc

    if not isinstance(response, SearchResponse):
        raise HTTPException(
            status_code=500,
            detail=(
                "SearchPipeline returned an unexpected response type: "
                f"{type(response).__name__}"
            ),
        )

    return _serialize(response)