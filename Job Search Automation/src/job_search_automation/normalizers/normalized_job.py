from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class NormalizedJob:
    """
    Provider-independent intermediate representation.

    Every provider converts its payload into this object.

    ONLY canonical_mapper.py is allowed to create Job().
    """

    searched_role: str

    title: str

    company: str

    location: str

    description: str

    job_url: str

    provider: str

    source: str

    posted_at: datetime | None = None

    employment_type: str | None = None

    seniority: str | None = None

    remote: bool = False

    work_mode: str | None = None

    salary_min: float | None = None

    salary_max: float | None = None

    currency: str | None = None

    salary_confidence: float | None = None

    skills: list[str] = field(default_factory=list)

    raw: dict[str, Any] = field(default_factory=dict)