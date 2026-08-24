from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ATSBoard:

    company: str

    ats: str

    board: str

    verified: bool = False