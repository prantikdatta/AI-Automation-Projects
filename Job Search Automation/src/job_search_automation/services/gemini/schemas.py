from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ==========================================================
# SKILL GAP
# ==========================================================

class SkillGap(BaseModel):
    """
    Represents a single missing or partially matching skill.
    """

    skill: str

    importance: str = Field(
        default="Medium",
        description="Critical | High | Medium | Low",
    )

    recommendation: str = ""


# ==========================================================
# RESUME IMPROVEMENT
# ==========================================================

class ResumeImprovement(BaseModel):
    """
    A suggested improvement to increase ATS or recruiter appeal.
    """

    section: str

    issue: str

    suggestion: str


# ==========================================================
# RESUME TAILORING
# ==========================================================

class ResumeTailoringResult(BaseModel):
    """
    AI-generated resume tailoring.
    """

    summary: str = ""

    key_changes: List[str] = Field(
        default_factory=list,
    )

    rewritten_bullets: List[str] = Field(
        default_factory=list,
    )

    ats_keywords: List[str] = Field(
        default_factory=list,
    )


# ==========================================================
# JOB ANALYSIS
# ==========================================================

class JobAnalysis(BaseModel):
    """
    AI analysis of the opportunity.
    """

    shortlist_score: float = Field(
        ge=0,
        le=100,
    )

    shortlist_bucket: str

    apply_priority: int = Field(
        ge=1,
        le=100,
    )

    recommendation: str

    blunt_reason: str

    strengths: List[str] = Field(
        default_factory=list,
    )

    concerns: List[str] = Field(
        default_factory=list,
    )

    missing_skills: List[SkillGap] = Field(
        default_factory=list,
    )

    resume_improvements: List[
        ResumeImprovement
    ] = Field(
        default_factory=list,
    )


# ==========================================================
# COVER LETTER
# ==========================================================

class CoverLetterResult(BaseModel):
    """
    AI-generated cover letter.
    """

    subject: str = ""

    body: str = ""


# ==========================================================
# INTERVIEW PREPARATION
# ==========================================================

class InterviewQuestion(BaseModel):
    """
    Interview question generated from the JD.
    """

    question: str

    answer: str


class InterviewPreparation(BaseModel):
    """
    AI-generated interview preparation.
    """

    questions: List[
        InterviewQuestion
    ] = Field(
        default_factory=list,
    )


# ==========================================================
# COMPLETE GEMINI RESPONSE
# ==========================================================

class GeminiResponse(BaseModel):
    """
    Complete structured response returned by Gemini.

    This schema acts as the contract between the LLM
    and the application.
    """

    analysis: JobAnalysis

    tailoring: Optional[
        ResumeTailoringResult
    ] = None

    cover_letter: Optional[
        CoverLetterResult
    ] = None

    interview: Optional[
        InterviewPreparation
    ] = None