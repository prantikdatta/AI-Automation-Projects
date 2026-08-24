from __future__ import annotations

from datetime import datetime
from datetime import timezone
from html import unescape
import re

from job_search_automation.ats.board import ATSBoard
from job_search_automation.models.job import Job


class GreenhouseAdapter:
    """
    Converts Greenhouse payload into canonical Job.
    """

    @staticmethod
    def _clean_html(text: str) -> str:
        if not text:
            return ""

        text = unescape(text)

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def normalize(
        board: ATSBoard,
        raw: dict,
    ) -> Job:
        location = ""

        if isinstance(raw.get("location"), dict):
            location = raw["location"].get(
                "name",
                "",
            )

        elif isinstance(raw.get("location"), str):
            location = raw["location"]

        description = GreenhouseAdapter._clean_html(
            raw.get("content")
            or raw.get("description")
            or ""
        )

        posted_at = datetime.now(
            timezone.utc
        )

        if raw.get("updated_at"):
            try:
                posted_at = datetime.fromisoformat(
                    raw["updated_at"].replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:
                pass

        return Job(
            searched_role=raw.get(
                "title",
                "",
            ),
            title=raw.get(
                "title",
                "",
            ),
            company=board.company,
            provider="greenhouse",
            source="greenhouse",
            description=description,
            location=location,
            job_url=raw.get(
                "absolute_url",
                "",
            ),
            posted_at=posted_at,
            salary_min=None,
            salary_max=None,
            currency=None,
            employment_type=None,
            seniority=None,
            work_mode=None,
            remote="remote" in location.lower(),
            skills=[],
            raw=raw,
        )