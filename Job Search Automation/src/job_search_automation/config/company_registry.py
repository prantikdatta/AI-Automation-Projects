from __future__ import annotations

from typing import TypedDict


class CompanyRegistryEntry(TypedDict):
    company: str
    ats: str
    board: str
    verified: bool


COMPANY_REGISTRY: list[CompanyRegistryEntry] = [
    # =====================
    # GREENHOUSE VERIFIED
    # =====================

    {
        "company": "Stripe",
        "ats": "greenhouse",
        "board": "stripe",
        "verified": True,
    },
    {
        "company": "Datadog",
        "ats": "greenhouse",
        "board": "datadog",
        "verified": True,
    },
    {
        "company": "Airbnb",
        "ats": "greenhouse",
        "board": "airbnb",
        "verified": True,
    },

    # =====================
    # LEVER
    # Awaiting verified boards
    # =====================

    {
        "company": "Figma",
        "ats": "lever",
        "board": "figma",
        "verified": False,
    },
    {
        "company": "GitLab",
        "ats": "lever",
        "board": "gitlab",
        "verified": False,
    },

    # =====================
    # ASHBY
    # Awaiting verified boards
    # =====================

    {
        "company": "OpenAI",
        "ats": "ashby",
        "board": "openai",
        "verified": False,
    },
    {
        "company": "Cursor",
        "ats": "ashby",
        "board": "cursor",
        "verified": False,
    },
]