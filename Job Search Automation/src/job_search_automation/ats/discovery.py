from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ATSDiscoveryResult:

    company: str

    ats: str

    board: str

    valid: bool

    job_count: int