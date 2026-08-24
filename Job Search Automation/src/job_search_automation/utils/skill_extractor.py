from __future__ import annotations

import re
from typing import List


class SkillExtractor:
    """
    Provider-independent deterministic skill extractor.

    Every provider passes only the job description.

    description
        ↓
    extract()
        ↓
    List[str]
    """

    SKILL_LIBRARY = {
        "python",
        "sql",
        "power bi",
        "tableau",
        "excel",
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "spark",
        "pyspark",
        "databricks",
        "snowflake",
        "aws",
        "azure",
        "gcp",
        "airflow",
        "docker",
        "kubernetes",
        "git",
        "github",
        "gitlab",
        "jira",
        "confluence",
        "linux",
        "bash",
        "shell scripting",
        "postgresql",
        "mysql",
        "sql server",
        "oracle",
        "mongodb",
        "redis",
        "bigquery",
        "looker",
        "looker studio",
        "ssis",
        "ssrs",
        "ssas",
        "dax",
        "power query",
        "m language",
        "etl",
        "elt",
        "data warehouse",
        "data modeling",
        "dimensional modeling",
        "star schema",
        "snowflake schema",
        "business intelligence",
        "analytics",
        "data analysis",
        "machine learning",
        "deep learning",
        "statistics",
        "forecasting",
        "a/b testing",
        "experimentation",
        "cohort analysis",
        "funnel analysis",
        "product analytics",
        "credit risk",
        "risk analytics",
        "fraud analytics",
        "predictive modeling",
        "feature engineering",
        "nlp",
        "genai",
        "llm",
        "openai",
        "gemini",
        "langchain",
        "fastapi",
        "flask",
        "streamlit",
        "rest api",
        "api",
        "microservices",
        "agile",
        "scrum",
        "stakeholder management",
        "program management",
        "project management",
        "pmo",
        "business analysis",
    }

    @classmethod
    def extract(
        cls,
        description: str | None,
    ) -> List[str]:

        if not description:
            return []

        text = description.lower()

        text = re.sub(
            r"[^\w\s\+\-\.#]",
            " ",
            text,
        )

        found = []

        for skill in sorted(cls.SKILL_LIBRARY):

            pattern = (
                r"\b"
                + re.escape(skill)
                + r"\b"
            )

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                found.append(skill)

        return sorted(set(found))