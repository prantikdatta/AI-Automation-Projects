from __future__ import annotations

import json
from pathlib import Path

from job_search_automation.profile.models import (
    ResumeProfile,
)


class ResumeProfileLoader:

    _profile = None

    @classmethod
    def load(
        cls,
    ) -> ResumeProfile:

        if cls._profile:

            return cls._profile

        path = (
            Path(__file__)
            .parent
            / "profile.json"
        )

        with open(
            path,
            encoding="utf-8",
        ) as file:

            cls._profile = ResumeProfile(

                **json.load(file)

            )

        return cls._profile