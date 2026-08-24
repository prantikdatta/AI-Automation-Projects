from __future__ import annotations


class JobBucketClassifier:
    """
    Maps a job into a high-level job bucket.

    This classifier is intentionally provider-independent.

    Every provider benefits automatically.
    """

    BUCKETS = {

        "Product Analytics": (

            "product analyst",
            "product analytics",
            "growth analyst",
            "growth analytics",
            "customer analytics",
            "business insights",

        ),

        "Business Intelligence": (

            "power bi",
            "tableau",
            "bi developer",
            "business intelligence",
            "analytics engineer",
            "report developer",
            "dashboard",

        ),

        "Data Analytics": (

            "data analyst",
            "analytics",
            "sql analyst",
            "business analyst",

        ),

        "Data Science": (

            "data scientist",
            "machine learning",
            "ml engineer",
            "ai engineer",
            "deep learning",
            "computer vision",
            "nlp",

        ),

        "Data Engineering": (

            "data engineer",
            "etl",
            "spark",
            "databricks",
            "airflow",
            "snowflake",
            "hadoop",
            "bigquery",

        ),

        "PMO / Strategy": (

            "program manager",
            "project manager",
            "pmo",
            "strategy",
            "consultant",
            "transformation",
            "governance",

        ),

        "Risk / Finance": (

            "credit risk",
            "risk analyst",
            "fraud",
            "finance analyst",
            "financial analyst",
            "treasury",

        ),

    }

    @classmethod
    def classify(

        cls,

        title: str | None,

        description: str | None,

    ) -> str:

        text = f"{title or ''} {description or ''}".lower()

        for bucket, keywords in cls.BUCKETS.items():

            for keyword in keywords:

                if keyword in text:

                    return bucket

        return "Other"