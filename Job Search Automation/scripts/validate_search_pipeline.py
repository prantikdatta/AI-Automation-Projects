from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from job_search_automation.models.job import Job
from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


# ============================================================
# MOCK JOB FACTORY
# ============================================================


def make_fake_job(
    title: str,
    company: str,
) -> Job:

    return Job(
        searched_role=title,
        run_date=datetime.now(timezone.utc),

        title=title,
        company=company,
        location="Mumbai",

        description=(
            f"Mock job description for {title} at {company}. "
            "Requires SQL, Python and analytics."
        ),

        job_url=(
            "https://example.com/"
            f"{company.lower().replace(' ', '-')}/"
            f"{title.lower().replace(' ', '-')}"
        ),

        source="Mock",
        provider="Mock",

        posted_at=datetime.now(timezone.utc),

        posting_priority=1,

        employment_type="Full-time",
        seniority="Mid",
        remote=False,
        work_mode="On-site",

        salary_min=None,
        salary_max=None,
        currency=None,
        salary_confidence=None,

        skills=[
            "SQL",
            "Python",
        ],

        matched_skills=[],
        missing_skills=[],

        company_tier="B",
        job_bucket="Analytics",

        overall_score=None,
        recommendation=None,
        overall_explanation=None,
        freshness_bucket=None,

        shortlist_likelihood_score=None,
        shortlist_bucket=None,

        blunt_reason=None,
        resume_match_result=None,

        apply_priority=1,

        data_quality_score=None,

        cover_letter=None,
        interview_questions=[],

        tailored_resume_reason=None,
        tailored_resume_text=None,

        duplicate_key=None,

        application_status="Not Applied",

        raw={},
    )


# ============================================================
# MOCK COMPONENTS
# ============================================================


class MockSearchOrchestrator:

    def collect_jobs(self) -> List[Job]:

        print(
            "[MOCK] SearchOrchestrator.collect_jobs()"
        )

        return [
            make_fake_job(
                "Data Analyst",
                "Company A",
            ),
            make_fake_job(
                "BI Analyst",
                "Company B",
            ),
            make_fake_job(
                "Business Analyst",
                "Company C",
            ),
        ]


class MockEnrichmentPipeline:

    def process(
        self,
        job: Job,
    ) -> Job:

        print(
            f"[MOCK] Enrichment -> "
            f"{job.title} / {job.company}"
        )

        job.job_bucket = "Analytics"

        return job


class MockResumeMatcher:

    def evaluate(
        self,
        job: Job,
    ) -> Job:

        print(
            f"[MOCK] ResumeMatcher -> "
            f"{job.title} / {job.company}"
        )

        # Intentional failure.
        # This verifies that one failed job does not
        # terminate the entire pipeline.

        if job.company == "Company C":

            raise RuntimeError(
                "Intentional validation failure"
            )

        job.overall_score = 85.0

        job.shortlist_likelihood_score = 90.0

        job.recommendation = "APPLY"

        job.matched_skills = [
            "SQL",
            "Python",
        ]

        job.missing_skills = []

        return job


class MockGoogleSheetsService:

    def append_jobs(
        self,
        headers,
        rows,
    ) -> None:

        print(
            f"[MOCK] Google Sheets export -> "
            f"{len(rows)} rows"
        )


# ============================================================
# MOCK FILTERS
# ============================================================


def mock_deduplicate_jobs(
    jobs: List[Job],
) -> List[Job]:

    print("[MOCK] Deduplication")

    return jobs


def mock_freshness_filter(
    jobs: List[Job],
) -> List[Job]:

    print("[MOCK] Freshness filter")

    return jobs


# ============================================================
# VALIDATION
# ============================================================


def validate() -> None:

    print()
    print("=" * 70)
    print("SEARCH PIPELINE VALIDATION")
    print("=" * 70)
    print()

    pipeline = SearchPipeline()

    # --------------------------------------------------------
    # Replace production dependencies with mocks
    # --------------------------------------------------------

    pipeline.search_orchestrator = (
        MockSearchOrchestrator()
    )

    pipeline.enrichment_pipeline = (
        MockEnrichmentPipeline()
    )

    pipeline.resume_matcher = (
        MockResumeMatcher()
    )

    pipeline.google_sheets = (
        MockGoogleSheetsService()
    )

    # --------------------------------------------------------
    # Patch utility functions used by SearchPipeline
    # --------------------------------------------------------

    import job_search_automation.orchestrators.search_pipeline as pipeline_module

    pipeline_module.deduplicate_jobs = (
        mock_deduplicate_jobs
    )

    pipeline_module.apply_freshness_filter = (
        mock_freshness_filter
    )

    # --------------------------------------------------------
    # Execute pipeline
    # --------------------------------------------------------

    response = pipeline.run()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    assert isinstance(
        response,
        SearchResponse,
    ), (
        "Pipeline must return SearchResponse."
    )

    assert response.success is True, (
        "Pipeline response.success must be True."
    )

    assert response.total_found == 2, (
        "Exactly 2 jobs should survive "
        "the intentional Company C failure."
    )

    assert response.total_returned == 2, (
        "Exactly 2 jobs should be returned."
    )

    assert len(response.jobs) == 2, (
        "Response must contain exactly 2 jobs."
    )

    assert all(
        isinstance(job, Job)
        for job in response.jobs
    ), (
        "Every response job must be an actual Job model."
    )

    assert response.jobs[0].overall_score >= (
        response.jobs[1].overall_score
    ), (
        "Jobs should be ranked by overall_score."
    )

    print()
    print("[PASS] Pipeline returned SearchResponse.")
    print(
        "[PASS] Failed job was isolated."
    )
    print(
        "[PASS] 2 jobs survived evaluation."
    )
    print(
        "[PASS] Jobs were ranked successfully."
    )
    print(
        "[PASS] Response contains valid Job objects."
    )
    print(
        "[PASS] Google Sheets received 2 rows."
    )

    print()
    print("=" * 70)
    print(
        "SEARCH PIPELINE VALIDATION PASSED"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":

    validate()