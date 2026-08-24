from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Job(BaseModel):
    """
    Canonical Job model.

    Provider
        ↓
    Normalization
        ↓
    Deduplication
        ↓
    Deterministic Intelligence
        ↓
    Gemini Enrichment
        ↓
    Resume Tailoring
        ↓
    Google Sheets
        ↓
    Application Tracking
    """

    # ==========================================================
    # SEARCH METADATA
    # ==========================================================

    searched_role: str

    run_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ==========================================================
    # BASIC JOB DETAILS
    # ==========================================================

    title: str

    company: str

    location: str

    description: str = ""

    job_url: str

    source: str

    provider: str

    posted_at: datetime | None = None

    posting_priority: int = 0

    # ==========================================================
    # JOB ATTRIBUTES
    # ==========================================================

    employment_type: str | None = None

    seniority: str | None = None

    remote: bool = False

    work_mode: str | None = None

    # ==========================================================
    # SALARY
    # ==========================================================

    salary_min: float | None = None

    salary_max: float | None = None

    currency: str | None = None

    salary_confidence: float | None = None

    # ==========================================================
    # SKILLS
    # ==========================================================

    skills: list[str] = Field(
        default_factory=list
    )

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    # ==========================================================
    # COMPANY
    # ==========================================================

    company_tier: str | None = None

    job_bucket: str | None = None

    # ==========================================================
    # DETERMINISTIC INTELLIGENCE
    # ==========================================================

    overall_score: float | None = None

    recommendation: str | None = None

    overall_explanation: str | None = None

    freshness_bucket: str | None = None

    # ==========================================================
    # AI ENRICHMENT
    # ==========================================================

    shortlist_likelihood_score: float | None = None

    shortlist_bucket: str | None = None

    blunt_reason: str | None = None

    resume_match_result: dict[str, Any] | None = None

    apply_priority: int | None = None

    data_quality_score: float | None = None

    cover_letter: str | None = None

    interview_questions: list[str] = Field(
        default_factory=list
    )

    # ==========================================================
    # RESUME TAILORING
    # ==========================================================

    tailored_resume_reason: str | None = None

    tailored_resume_text: str | None = None

    # ==========================================================
    # DEDUPLICATION
    # ==========================================================

    duplicate_key: str | None = None

    # ==========================================================
    # APPLICATION TRACKING
    # ==========================================================

    application_status: str = "Not Applied"

    # ==========================================================
    # FINAL SELECTION
    # ==========================================================

    final_selection_eligible: bool = False

    final_selection_bucket: str | None = None

    final_selection_reason: str | None = None

    final_selection_priority: int = 0

    # ==========================================================
    # RAW PROVIDER PAYLOAD
    # ==========================================================

    raw: dict[str, Any] = Field(
        default_factory=dict
    )