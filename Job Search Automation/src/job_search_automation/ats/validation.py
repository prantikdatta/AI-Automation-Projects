from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ATSBoardValidation:

    company: str

    ats: str

    board: str

    active: bool

    job_count: int