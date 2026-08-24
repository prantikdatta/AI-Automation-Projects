from __future__ import annotations

from collections import Counter

from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


def main() -> None:
    print()
    print("=" * 70)
    print("END-TO-END PIPELINE VALIDATION")
    print("=" * 70)

    pipeline = SearchPipeline()

    print("[INFO] Running real SearchPipeline...")

    response = pipeline.run()

    # ------------------------------------------------------------
    # 1. RESPONSE VALIDATION
    # ------------------------------------------------------------

    if not isinstance(response, SearchResponse):
        raise AssertionError(
            "SearchPipeline.run() did not return SearchResponse."
        )

    print("[PASS] SearchPipeline returned SearchResponse.")

    # ------------------------------------------------------------
    # 2. JOB OUTPUT VALIDATION
    # ------------------------------------------------------------

    jobs = response.jobs

    if jobs is None:
        raise AssertionError(
            "SearchResponse.jobs is None."
        )

    print(f"[INFO] Final jobs: {len(jobs)}")

    if not jobs:
        raise AssertionError(
            "Pipeline returned zero final jobs."
        )

    print("[PASS] Final job collection is non-empty.")

    # ------------------------------------------------------------
    # 3. REQUIRED CANONICAL FIELDS
    # ------------------------------------------------------------

    required_fields = (
        "title",
        "company",
        "location",
        "job_url",
        "source",
        "provider",
        "searched_role",
    )

    missing_fields: Counter[str] = Counter()

    for index, job in enumerate(jobs, start=1):
        for field in required_fields:
            value = getattr(job, field, None)

            if value is None or (
                isinstance(value, str)
                and not value.strip()
            ):
                missing_fields[field] += 1

                print(
                    f"[FAIL] Job #{index} missing '{field}': "
                    f"title={getattr(job, 'title', None)!r}, "
                    f"url={getattr(job, 'job_url', None)!r}"
                )

    if missing_fields:
        raise AssertionError(
            "Required canonical fields missing: "
            + ", ".join(
                f"{field}={count}"
                for field, count in missing_fields.items()
            )
        )

    print("[PASS] All final jobs contain required canonical fields.")

    # ------------------------------------------------------------
    # 4. URL VALIDATION
    # ------------------------------------------------------------

    empty_urls = [
        job
        for job in jobs
        if not job.job_url
        or not job.job_url.strip()
    ]

    if empty_urls:
        raise AssertionError(
            f"{len(empty_urls)} final jobs have empty job_url."
        )

    print("[PASS] All final jobs contain job URLs.")

    # ------------------------------------------------------------
    # 5. DUPLICATE URL VALIDATION
    # ------------------------------------------------------------

    normalized_urls = [
        job.job_url.strip().lower().rstrip("/")
        for job in jobs
    ]

    duplicate_urls = [
        url
        for url, count in Counter(normalized_urls).items()
        if count > 1
    ]

    if duplicate_urls:
        raise AssertionError(
            "Duplicate job URLs remain in final output: "
            + ", ".join(duplicate_urls[:10])
        )

    print("[PASS] No duplicate job URLs remain.")

    # ------------------------------------------------------------
    # 6. PROVIDER DISTRIBUTION
    # ------------------------------------------------------------

    provider_counts = Counter(
        job.provider
        for job in jobs
        if job.provider
    )

    print()
    print("[INFO] Providers:")

    for provider, count in sorted(provider_counts.items()):
        print(f"       {provider}: {count}")

    if not provider_counts:
        raise AssertionError(
            "No provider information exists in final jobs."
        )

    print("[PASS] Provider information present.")

    # ------------------------------------------------------------
    # 7. SEARCHED ROLE DISTRIBUTION
    # ------------------------------------------------------------

    role_counts = Counter(
        job.searched_role
        for job in jobs
        if job.searched_role
    )

    print()
    print("[INFO] Searched roles:")

    for role, count in sorted(role_counts.items()):
        print(f"       {role}: {count}")

    if not role_counts:
        raise AssertionError(
            "No searched_role information exists in final jobs."
        )

    print("[PASS] searched_role information present.")

    # ------------------------------------------------------------
    # 8. FINAL JOB SAMPLE
    # ------------------------------------------------------------

    print()
    print("[INFO] Final job sample:")

    for job in jobs[:10]:
        print(
            f"       {job.title} | "
            f"{job.company} | "
            f"{job.location} | "
            f"{job.provider}"
        )

    # ------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------

    print()
    print("=" * 70)
    print("END-TO-END PIPELINE VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()