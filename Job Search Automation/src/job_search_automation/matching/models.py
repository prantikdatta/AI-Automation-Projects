from __future__ import annotations

from pydantic import BaseModel


class MatchResult(BaseModel):

    score: int

    matched_skills: list[str]

    missing_skills: list[str]

    strengths: list[str]

    weaknesses: list[str]

    recommendation: str

    skill_score: int

    role_score: int

    location_score: int

    experience_score: int