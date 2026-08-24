from __future__ import annotations

from job_search_automation.models.job import Job


class AnalyticsJobFilter:
    """
    Filters jobs relevant to the user's profile.

    A job is retained if either:
    1. The title matches analytics-related keywords.
    2. The description matches analytics-related keywords.
    """

    TITLE_KEYWORDS = {
        "data analyst",
        "business analyst",
        "business intelligence",
        "bi analyst",
        "bi developer",
        "analytics",
        "analytics engineer",
        "analytics consultant",
        "product analyst",
        "data scientist",
        "reporting analyst",
        "reporting",
        "insights",
        "strategy",
        "decision science",
        "risk analyst",
        "credit risk",
        "fraud",
        "data engineer",
        "power bi",
        "sql",
    }

    DESCRIPTION_KEYWORDS = {
        "python",
        "sql",
        "power bi",
        "tableau",
        "dashboard",
        "analytics",
        "business intelligence",
        "reporting",
        "etl",
        "data warehouse",
        "stakeholder",
        "excel",
        "data analysis",
        "forecasting",
        "statistics",
        "visualization",
        "predictive",
        "machine learning",
    }

    @classmethod
    def keep(cls, job: Job) -> bool:

        title = (job.title or "").lower()

        description = (job.description or "").lower()

        for keyword in cls.TITLE_KEYWORDS:

            if keyword in title:
                return True

        for keyword in cls.DESCRIPTION_KEYWORDS:

            if keyword in description:
                return True

        return False

    @classmethod
    def filter(
        cls,
        jobs: list[Job],
    ) -> list[Job]:

        return [
            job
            for job in jobs
            if cls.keep(job)
        ]