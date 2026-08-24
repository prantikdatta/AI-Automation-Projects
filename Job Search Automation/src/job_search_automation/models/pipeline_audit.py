from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NOT_EVALUATED = "not_evaluated"


class PipelineStage(str, Enum):
    SEARCH = "search"
    VALIDATION = "validation"
    DEDUPLICATION = "deduplication"
    FRESHNESS = "freshness"
    RELEVANCE = "relevance"
    LOCATION = "location"
    SCORING = "scoring"
    ENRICHMENT = "enrichment"
    RESUME_MATCH = "resume_match"
    RANKING = "ranking"
    FINAL_SELECTION = "final_selection"
    EXPORT = "export"


class PipelineStageResult(BaseModel):
    stage: PipelineStage
    status: PipelineStatus
    reason: str | None = None
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    metadata: dict[str, object] = Field(default_factory=dict)


class JobPipelineAudit(BaseModel):
    job_id: str
    source: str

    company: str | None = None
    title: str | None = None
    location: str | None = None
    job_url: str | None = None
    posted_at: datetime | None = None

    run_id: str | None = None

    searched_role: str | None = None
    searched_location: str | None = None
    search_bucket: str | None = None
    search_priority: int | None = None

    stages: list[PipelineStageResult] = Field(
        default_factory=list
    )

    current_stage: PipelineStage = PipelineStage.SEARCH
    current_status: PipelineStatus = PipelineStatus.PENDING

    final_score: float | None = None
    final_rank: int | None = None
    final_bucket: str | None = None
    final_status: str | None = None

    def record(
        self,
        stage: PipelineStage,
        status: PipelineStatus,
        reason: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        result = PipelineStageResult(
            stage=stage,
            status=status,
            reason=reason,
            metadata=metadata or {},
        )

        self.stages.append(result)

        self.current_stage = stage
        self.current_status = status

    def latest_result(
        self,
        stage: PipelineStage,
    ) -> PipelineStageResult | None:
        for result in reversed(self.stages):
            if result.stage == stage:
                return result

        return None

    def has_passed(
        self,
        stage: PipelineStage,
    ) -> bool:
        result = self.latest_result(stage)

        return (
            result is not None
            and result.status == PipelineStatus.PASSED
        )

    def has_failed(
        self,
        stage: PipelineStage,
    ) -> bool:
        result = self.latest_result(stage)

        return (
            result is not None
            and result.status
            in {
                PipelineStatus.REJECTED,
                PipelineStatus.DUPLICATE,
            }
        )