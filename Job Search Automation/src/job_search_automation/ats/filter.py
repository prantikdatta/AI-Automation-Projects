from __future__ import annotations

from datetime import datetime, timedelta


class ATSJobFilter:
    """
    Filters ATS jobs before expensive processing.
    """


    def __init__(
        self,
        target_locations: list[str] | None = None,
        keywords: list[str] | None = None,
    ):
        self.target_locations = (
            target_locations or []
        )

        self.keywords = (
            keywords or []
        )


    def matches_location(
        self,
        job,
    ) -> bool:

        if not self.target_locations:
            return True

        if not job.location:
            return False

        location = (
            job.location.lower()
        )

        return any(
            loc.lower() in location
            for loc in self.target_locations
        )


    def matches_role(
        self,
        job,
    ) -> bool:

        if not self.keywords:
            return True

        text = (
            f"{job.title} "
            f"{job.searched_role}"
        ).lower()

        return any(
            keyword.lower()
            in text
            for keyword in self.keywords
        )


    def filter(
        self,
        jobs: list,
    ) -> list:

        return [
            job
            for job in jobs
            if (
                self.matches_location(job)
                and
                self.matches_role(job)
            )
        ]