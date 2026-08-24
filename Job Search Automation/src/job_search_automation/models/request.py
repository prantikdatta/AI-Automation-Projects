from __future__ import annotations

from typing import List

from pydantic import BaseModel
from pydantic import Field


class SearchRequest(BaseModel):
    """
    Canonical search request shared by every provider.

    Supports both:

    • Legacy single-role providers
    • New bucket-based search engine
    """

    # ----------------------------------------------------------
    # Legacy (Backward Compatible)
    # ----------------------------------------------------------

    searched_role: str

    keywords: List[str]

    locations: List[str]

    # ----------------------------------------------------------
    # New Intelligent Search
    # ----------------------------------------------------------

    bucket: str = ""

    roles: List[str] = Field(
        default_factory=list,
    )

    priority: int = 1

    # ----------------------------------------------------------
    # Search Controls
    # ----------------------------------------------------------

    limit: int = Field(
        default=25,
        ge=1,
        le=100,
    )

    remote_only: bool = False

    posted_within_days: int | None = Field(
        default=7,
        ge=1,
        le=30,
    )

    providers: List[str] = Field(
        default_factory=list,
    )