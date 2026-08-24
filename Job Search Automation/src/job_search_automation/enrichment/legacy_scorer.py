from __future__ import annotations

from datetime import datetime, timezone

from job_search_automation.models.job import Job


class JobScorer:
    """
    Deterministic job scoring engine.

    Produces:
    - overall_score
    - recommendation
    - apply_priority
    - explanation
    """

    ROLE_SCORES = {
        "Strategy Analytics": 30,
        "Product Analytics": 30,
        "BI Engineer / Analyst": 28,
        "Data Analyst": 25,
        "Risk Analyst": 25,
        "Data Engineer": 22,
        "Program Manager / TPM": 22,
    }

    COMPANY_SCORES = {
        "Tier 1": 5,
        "Tier 2": 3,
        "Unknown": 1,
    }


    @classmethod
    def score(
        cls,
        job: Job,
    ) -> Job:

        score = 0
        reasons = []


        # ------------------------------------------
        # Role Match
        # ------------------------------------------

        role_score = cls.ROLE_SCORES.get(
            job.job_bucket or "",
            10,
        )

        score += role_score

        if job.job_bucket:
            reasons.append(
                f"Strong role alignment: {job.job_bucket}"
            )


        # ------------------------------------------
        # Skills Match
        # ------------------------------------------

        if job.skills:

            skill_score = min(
                len(job.skills) * 5,
                30,
            )

            score += skill_score

            reasons.append(
                f"{len(job.skills)} relevant skills detected"
            )


        # ------------------------------------------
        # Seniority
        # ------------------------------------------

        if job.seniority == "Senior":

            score += 15

            reasons.append(
                "Senior-level alignment"
            )

        elif job.seniority == "Mid":

            score += 10


        # ------------------------------------------
        # Location
        # ------------------------------------------

        location = (
            job.location
            .lower()
        )

        if any(
            x in location
            for x in [
                "remote",
                "bangalore",
                "bengaluru",
                "mumbai",
                "hyderabad",
            ]
        ):

            score += 10

            reasons.append(
                "Preferred location"
            )


        # ------------------------------------------
        # Freshness
        # ------------------------------------------

        if job.posted_at:

            days_old = (
                datetime.now(timezone.utc)
                -
                job.posted_at
            ).days


            if days_old <= 3:

                score += 10

                job.freshness_bucket = "Fresh"


            elif days_old <= 30:

                score += 5

                job.freshness_bucket = "Recent"

        else:

            job.freshness_bucket = "Unknown"


        # ------------------------------------------
        # Company Tier
        # ------------------------------------------

        score += cls.COMPANY_SCORES.get(
            job.company_tier or "",
            1,
        )


        # ------------------------------------------
        # Final Output
        # ------------------------------------------

        job.overall_score = min(
            score,
            100,
        )


        if job.overall_score >= 80:

            job.recommendation = "Apply"

            job.apply_priority = 1


        elif job.overall_score >= 60:

            job.recommendation = "Review"

            job.apply_priority = 2


        else:

            job.recommendation = "Low Priority"

            job.apply_priority = 3


        job.overall_explanation = (
            "; ".join(reasons)
        )


        return job