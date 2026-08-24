from __future__ import annotations

import re

from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest


class RoleMatcher:
    """
    Centralized relevance engine.

    Every provider uses this class before sending
    jobs to the resume scorer.

    Output
    ------
    score : integer

    Higher score
        more relevant

    Lower score
        reject.
    """

    POSITIVE_WEIGHTS = {

        # Core roles

        "credit risk analyst": 20,
        "risk analyst": 20,
        "fraud analyst": 18,
        "risk consultant": 18,
        "business analyst": 15,
        "product analyst": 15,
        "data analyst": 15,
        "analytics engineer": 15,
        "business intelligence": 15,

        # Skills

        "sql": 8,
        "python": 8,
        "power bi": 8,
        "tableau": 6,
        "dashboards": 5,
        "analytics": 5,

        # Domains

        "bank": 6,
        "banking": 6,
        "fintech": 8,
        "payments": 8,
        "fraud": 7,
        "risk": 7,
        "credit": 7,
        "insurance": 5,
        "marketing" : 5,
        
    }

    NEGATIVE_WEIGHTS = {

        "copywriter": -40,
        "seo": -35,
        "sales": -35,
        "graphic designer": -40,
        "designer": -30,
        "recruiter": -40,
        "human resources": -40,
        "hr": -35,
        "doctor": -50,
        "nurse": -50,
        "civil engineer": -40,
        "mechanical engineer": -35,
    }

    MINIMUM_SCORE = 15

    @staticmethod
    def normalize(text: str) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9 ]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @classmethod
    def calculate_score(
        cls,
        job: Job,
        request: SearchRequest,
    ) -> int:

        searchable = cls.normalize(

            f"{job.title} {job.description}"

        )

        score = 0

        for phrase, weight in cls.POSITIVE_WEIGHTS.items():

            if phrase in searchable:

                score += weight

        for phrase, penalty in cls.NEGATIVE_WEIGHTS.items():

            if phrase in searchable:

                score += penalty

        for keyword in request.keywords:

            keyword = cls.normalize(keyword)

            if keyword in searchable:

                score += 10

        return max(score, 0)

    @classmethod
    def is_relevant(
        cls,
        job: Job,
        request: SearchRequest,
    ) -> bool:

        return (

            cls.calculate_score(
                job,
                request,
            )

            >= cls.MINIMUM_SCORE

        )