from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ResumeProfile:

    skills: list[str]

    target_roles: list[str]

    preferred_locations: list[str]

    experience_years: float

    preferred_work_modes: list[str]