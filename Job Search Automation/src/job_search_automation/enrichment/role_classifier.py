from __future__ import annotations

import re

from job_search_automation.models.job import Job


class RoleClassifier:
    """
    Deterministic job role classification.

    Maps title + description into target job buckets.
    """

    ROLE_PATTERNS = {
        "Strategy Analytics": [
            "strategy",
            "analytics business partner",
            "business analytics",
            "analytics consultant",
            "decision science",
        ],
        "Product Analytics": [
            "product analyst",
            "product analytics",
            "growth analytics",
            "customer analytics",
        ],
        "BI Engineer / Analyst": [
            "business intelligence",
            "bi analyst",
            "power bi",
            "tableau",
            "dashboard",
            "reporting analyst",
        ],
        "Data Analyst": [
            "data analyst",
            "analytics analyst",
            "reporting analyst",
        ],
        "Data Engineer": [
            "data engineer",
            "etl",
            "pipeline",
            "spark",
            "databricks",
        ],
        "Risk Analyst": [
            "risk analyst",
            "credit risk",
            "fraud",
            "underwriting",
        ],
        "Program Manager / TPM": [
            "program manager",
            "technical program manager",
            "tpm",
            "project manager",
        ],
    }

    SENIORITY_PATTERNS = {
        "Entry": [
            "intern",
            "junior",
            "associate",
        ],
        "Mid": [
            "analyst",
            "engineer",
            "specialist",
        ],
        "Senior": [
            "senior",
            "lead",
            "principal",
            "manager",
        ],
        "Executive": [
            "director",
            "head",
            "vp",
        ],
    }

    @classmethod
    def classify(
        cls,
        job: Job,
    ) -> Job:

        text = (
            f"{job.title} {job.description}"
        ).lower()

        # Role bucket

        for bucket, patterns in cls.ROLE_PATTERNS.items():

            for pattern in patterns:

                if re.search(
                    re.escape(pattern),
                    text,
                ):
                    job.job_bucket = bucket
                    break

            if job.job_bucket:
                break


        # Seniority

        for level, patterns in cls.SENIORITY_PATTERNS.items():

            for pattern in patterns:

                if re.search(
                    re.escape(pattern),
                    text,
                ):
                    job.seniority = level
                    break

            if job.seniority:
                break


        return job