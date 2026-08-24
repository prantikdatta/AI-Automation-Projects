from __future__ import annotations

from pydantic import BaseModel


class ResumeProfile(BaseModel):

    name: str

    experience_years: float

    skills: list[str]

    preferred_locations: list[str]

    preferred_roles: list[str]

    domains: list[str]

    certifications: list[str]