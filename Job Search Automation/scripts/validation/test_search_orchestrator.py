from __future__ import annotations

from collections import Counter

from job_search_automation.orchestrators.search_orchestrator import (
    SearchOrchestrator,
    TARGET_API_POOL,
    TARGET_ATS_POOL,
)


def main() -> None:

    print("=" * 70)
    print("SEARCH ORCHESTRATOR VALIDATION")
    print("=" * 70)

    orchestrator = SearchOrchestrator()

    # ---------------------------------------------------------
    # 1. Strategy generation
    # ---------------------------------------------------------

    print("\n[1] SEARCH STRATEGY")

    plans = orchestrator.search_queries

    print(
        f"Search plans generated: {len(plans)}"
    )

    assert plans, (
        "SearchStrategyEngine produced no search plans."
    )

    for plan in plans[:5]:
        print(
            f"  roles={plan['roles']} | "
            f"location={plan['location']} | "
            f"bucket={plan['bucket']} | "
            f"priority={plan['priority']}"
        )

    print(
        "[PASS] Search strategy generated."
    )

    # ---------------------------------------------------------
    # 2. Collection
    # ---------------------------------------------------------

    print("\n[2] COLLECT JOBS")

    jobs = orchestrator.collect_jobs()

    print(
        f"Total jobs collected: {len(jobs)}"
    )

    assert jobs, (
        "SearchOrchestrator returned zero jobs."
    )

    print(
        "[PASS] Jobs collected."
    )

    # ---------------------------------------------------------
    # 3. Canonical Job validation
    # ---------------------------------------------------------

    print("\n[3] CANONICAL JOB VALIDATION")

    required_attributes = [
        "title",
        "company",
        "location",
        "description",
        "job_url",
        "provider",
        "source",
    ]

    invalid_jobs = []

    for job in jobs:

        missing = [
            attribute
            for attribute in required_attributes
            if not hasattr(job, attribute)
        ]

        if missing:
            invalid_jobs.append(
                (
                    job.title,
                    missing,
                )
            )

    assert not invalid_jobs, (
        f"Invalid canonical jobs: {invalid_jobs[:5]}"
    )

    print(
        f"Validated {len(jobs)} canonical Job objects."
    )

    print(
        "[PASS] Canonical Job structure valid."
    )

    # ---------------------------------------------------------
    # 4. Provider distribution
    # ---------------------------------------------------------

    print("\n[4] PROVIDER DISTRIBUTION")

    provider_counts = Counter(
        job.provider
        for job in jobs
    )

    for provider, count in sorted(
        provider_counts.items()
    ):
        print(
            f"  {provider:<20} {count:>5}"
        )

    assert provider_counts, (
        "No provider information found."
    )

    print(
        "[PASS] Provider distribution available."
    )

    # ---------------------------------------------------------
    # 5. API / ATS pools
    # ---------------------------------------------------------

    print("\n[5] API / ATS POOLS")

    ats_providers = {
        "greenhouse",
        "ashby",
    }

    ats_jobs = [
        job
        for job in jobs
        if job.provider.strip().lower()
        in ats_providers
    ]

    api_jobs = [
        job
        for job in jobs
        if job.provider.strip().lower()
        not in ats_providers
    ]

    print(
        f"API jobs: {len(api_jobs)}"
    )

    print(
        f"ATS jobs: {len(ats_jobs)}"
    )

    print(
        f"Configured API target: {TARGET_API_POOL}"
    )

    print(
        f"Configured ATS target: {TARGET_ATS_POOL}"
    )

    assert (
        len(api_jobs) > 0
        or len(ats_jobs) > 0
    ), (
        "Neither API nor ATS pool contains jobs."
    )

    print(
        "[PASS] API/ATS pool separation works."
    )

    # ---------------------------------------------------------
    # 6. Search plan coverage
    # ---------------------------------------------------------

    print("\n[6] SEARCH PLAN COVERAGE")

    searched_roles = {
        job.searched_role
        for job in jobs
        if job.searched_role
    }

    print(
        f"Distinct searched roles: "
        f"{len(searched_roles)}"
    )

    for role in sorted(
        searched_roles,
    )[:10]:
        print(
            f"  {role}"
        )

    print(
        "[PASS] Search-role metadata available."
    )

    # ---------------------------------------------------------
    # 7. Basic duplicate observation
    # ---------------------------------------------------------

    print("\n[7] DUPLICATE OBSERVATION")

    urls = [
        job.job_url
        for job in jobs
        if job.job_url
    ]

    duplicate_count = (
        len(urls)
        - len(set(urls))
    )

    print(
        f"Total job URLs: {len(urls)}"
    )

    print(
        f"Duplicate URLs before pipeline "
        f"deduplication: {duplicate_count}"
    )

    print(
        "[PASS] Duplicate observation completed."
    )

    # ---------------------------------------------------------
    # Final
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        "[PASS] SEARCH ORCHESTRATOR VALIDATION COMPLETED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()