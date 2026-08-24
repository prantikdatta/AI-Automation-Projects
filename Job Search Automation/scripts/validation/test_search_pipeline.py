from __future__ import annotations

from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


def main() -> None:

    print("=" * 70)
    print("SEARCH PIPELINE VALIDATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Pipeline initialization
    # ---------------------------------------------------------

    print("\n[1] PIPELINE INITIALIZATION")

    pipeline = SearchPipeline()

    assert pipeline.search_orchestrator is not None
    assert pipeline.resume_matcher is not None
    assert pipeline.enrichment_pipeline is not None
    assert pipeline.google_sheets is not None

    print("[PASS] All pipeline components initialized.")

    # ---------------------------------------------------------
    # 2. Execute pipeline
    # ---------------------------------------------------------

    print("\n[2] PIPELINE EXECUTION")

    response = pipeline.run()

    assert isinstance(
        response,
        SearchResponse,
    )

    print(
        f"Provider: {response.provider}"
    )

    print(
        f"Success: {response.success}"
    )

    print(
        f"Total found: {response.total_found}"
    )

    print(
        f"Total returned: {response.total_returned}"
    )

    print(
        f"Message: {response.message}"
    )

    assert response.success is True

    print("[PASS] Pipeline executed successfully.")

    # ---------------------------------------------------------
    # 3. Response consistency
    # ---------------------------------------------------------

    print("\n[3] RESPONSE CONSISTENCY")

    assert (
        response.total_found
        == len(response.jobs)
    )

    assert (
        response.total_returned
        == len(response.jobs)
    )

    print(
        f"Response contains {len(response.jobs)} evaluated jobs."
    )

    print(
        "[PASS] SearchResponse counts are consistent."
    )

    # ---------------------------------------------------------
    # 4. Evaluated job validation
    # ---------------------------------------------------------

    print("\n[4] EVALUATED JOB VALIDATION")

    required_attributes = [
        "title",
        "company",
        "job_url",
        "provider",
        "overall_score",
        "posting_priority",
    ]

    invalid_jobs = []

    for job in response.jobs:

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(job, attribute)
        ]

        if missing:
            invalid_jobs.append(
                (
                    job.title,
                    job.company,
                    missing,
                )
            )

    assert not invalid_jobs, (
        "Jobs missing required evaluated fields: "
        f"{invalid_jobs[:5]}"
    )

    print(
        f"Validated {len(response.jobs)} evaluated jobs."
    )

    print(
        "[PASS] Evaluated Job objects are structurally valid."
    )

    # ---------------------------------------------------------
    # 5. Ranking validation
    # ---------------------------------------------------------

    print("\n[5] RANKING VALIDATION")

    scores = [
        job.overall_score
        for job in response.jobs
        if job.overall_score is not None
    ]

    assert len(scores) == len(response.jobs), (
        "Some jobs do not have an overall_score."
    )

    assert scores == sorted(
        scores,
        reverse=True,
    ), (
        "Jobs are not sorted by overall_score descending."
    )

    print(
        f"Highest score: {scores[0] if scores else 'N/A'}"
    )

    print(
        f"Lowest score: {scores[-1] if scores else 'N/A'}"
    )

    print(
        "[PASS] Jobs are ranked by overall_score."
    )

    # ---------------------------------------------------------
    # 6. Job sample
    # ---------------------------------------------------------

    print("\n[6] TOP JOBS")

    for index, job in enumerate(
        response.jobs[:10],
        start=1,
    ):

        print(
            f"{index:>2}. "
            f"{job.title} | "
            f"{job.company} | "
            f"score={job.overall_score} | "
            f"priority={job.posting_priority}"
        )

    # ---------------------------------------------------------
    # Final
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "[PASS] SEARCH PIPELINE VALIDATION COMPLETED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()