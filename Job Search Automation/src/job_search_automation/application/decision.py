from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ApplicationDecision(str, Enum):
    READY = "READY"
    READY_WITH_TAILORING = "READY_WITH_TAILORING"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"


class ApplicationReadinessResult(BaseModel):
    decision: ApplicationDecision

    eligible: bool

    reason: str

    checks: list[str] = Field(default_factory=list)

    missing_information: list[str] = Field(
        default_factory=list
    )

    recommended_actions: list[str] = Field(
        default_factory=list
    )