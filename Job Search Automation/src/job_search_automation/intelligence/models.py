from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BaseScoreResult(BaseModel):
    """
    Base result shared by deterministic scoring components.
    """

    score: float = 0.0

    explanation: str = ""

    confidence: float = 1.0

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SkillMatchResult(BaseScoreResult):
    """
    Result produced by SkillMatcher.
    """

    matched_skills: list[str] = Field(
        default_factory=list,
    )

    missing_skills: list[str] = Field(
        default_factory=list,
    )


class ExperienceMatchResult(BaseScoreResult):
    """
    Result produced by ExperienceMatcher.
    """

    required_years: float | None = None

    candidate_years: float | None = None

    experience_gap: float | None = None


class CareerProgressionResult(BaseScoreResult):
    """
    Result produced by CareerProgressionMatcher.
    """

    current_role: str = ""

    matched_role: str | None = None

    current_level: int = 0

    job_level: int | None = None

    level_difference: int | None = None

    recommendation: str = ""


class LocationMatchResult(BaseScoreResult):
    """
    Result produced by LocationMatcher.
    """

    location: str = ""

    preferred_location: bool = False

    remote_match: bool = False

    work_mode: str | None = None


class CompanyScoreResult(BaseScoreResult):
    """
    Result produced by CompanyScorer.
    """

    company_name: str = ""

    company_tier: str = "Other"

    industry: str | None = None

    normalized_company_name: str = ""


class FreshnessScoreResult(BaseScoreResult):
    """
    Result produced by FreshnessScorer.
    """

    age_hours: float = 0.0

    age_days: int = 0

    freshness_bucket: str = ""


class ResumeMatchResult(BaseModel):
    """
    Complete deterministic evaluation of a job.

    This object represents the final output of the
    deterministic intelligence engine before LLM enrichment.
    """

    overall_score: float = 0.0

    shortlist_bucket: str = ""

    apply_priority: int = 0

    recommendation: str = ""

    overall_explanation: str = ""

    skill_result: SkillMatchResult

    experience_result: ExperienceMatchResult

    career_result: CareerProgressionResult

    location_result: LocationMatchResult

    company_result: CompanyScoreResult

    freshness_result: FreshnessScoreResult


class FinalScoreResult(BaseModel):
    """
    Final deterministic ranking result used by the pipeline.
    """

    overall_score: float

    shortlist_bucket: str

    apply_priority: int

    recommendation: str

    explanation: str = ""