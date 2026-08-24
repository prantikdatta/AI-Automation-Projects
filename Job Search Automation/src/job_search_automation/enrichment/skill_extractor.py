from __future__ import annotations

import re

from job_search_automation.models.job import Job


class SkillExtractor:
    """
    Deterministic skill extraction from job descriptions.

    Extracts known technical and analytics skills
    before AI enrichment.
    """

    SKILL_MAP = {
        "python": "Python",
        "sql": "SQL",
        "power bi": "Power BI",
        "tableau": "Tableau",
        "excel": "Excel",
        "databricks": "Databricks",
        "spark": "Apache Spark",
        "pyspark": "PySpark",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "Google Cloud",
        "snowflake": "Snowflake",
        "machine learning": "Machine Learning",
        "statistics": "Statistics",
        "data analysis": "Data Analysis",
        "analytics": "Analytics",
        "product analytics": "Product Analytics",
        "business intelligence": "Business Intelligence",
        "etl": "ETL",
        "data engineering": "Data Engineering",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "terraform": "Terraform",
        "java": "Java",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "node": "Node.js",
        "api": "API",
        "rest": "REST API",
        "graphql": "GraphQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "oracle": "Oracle",
        "teradata": "Teradata",
    }

    @classmethod
    def extract(
        cls,
        job: Job,
    ) -> Job:
        """
        Extract skills and update Job object.
        """

        description = (
            job.description
            .lower()
        )

        skills = set()

        for keyword, label in cls.SKILL_MAP.items():

            pattern = (
                r"\b"
                + re.escape(keyword)
                + r"\b"
            )

            if re.search(
                pattern,
                description,
            ):
                skills.add(label)

        job.skills = sorted(skills)

        return job