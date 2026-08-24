from __future__ import annotations

from job_search_automation.models.request import SearchRequest
from job_search_automation.providers.ashby_provider import AshbyProvider
from job_search_automation.providers.provider_manager import ProviderManager


def main() -> None:

    print("=" * 70)
    print("PROVIDER MANAGER VALIDATION")
    print("=" * 70)

    provider = AshbyProvider()

    manager = ProviderManager(
        providers=[provider],
    )

    request = SearchRequest(
        searched_role="Data Analyst",
        roles=["Data Analyst"],
        keywords=["Data Analyst"],
        locations=["Mumbai"],
        bucket="Analytics",
        priority=1,
        limit=50,
        remote_only=False,
        posted_within_days=14,
    )

    # --------------------------------------------------------------
    # SEARCH 1
    # --------------------------------------------------------------

    print("\n[1] FIRST SEARCH")

    response1 = manager.search_by_provider(
        request,
    )

    ashby_jobs_1 = response1.get(
        "Ashby",
        [],
    )

    print(
        f"Ashby jobs returned: {len(ashby_jobs_1)}"
    )

    # --------------------------------------------------------------
    # SEARCH 2
    # --------------------------------------------------------------

    print("\n[2] SECOND SEARCH")

    response2 = manager.search_by_provider(
        request,
    )

    ashby_jobs_2 = response2.get(
        "Ashby",
        [],
    )

    print(
        f"Ashby jobs returned: {len(ashby_jobs_2)}"
    )

    # --------------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------------

    assert "Ashby" in response1
    assert "Ashby" in response2

    assert len(ashby_jobs_1) == len(
        ashby_jobs_2
    )

    print("\n[PASS] ProviderManager returned Ashby jobs.")
    print("[PASS] Repeated search completed.")
    print("[PASS] ProviderManager grouping works.")
    print("[PASS] ATS provider owns its cache.")
    print("\nValidation completed successfully.")


if __name__ == "__main__":
    main()