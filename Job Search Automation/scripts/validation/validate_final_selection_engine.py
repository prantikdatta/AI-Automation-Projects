from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Repository import setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.intelligence.final_selector import (
    FinalSelectionEngine,
)


def make_job(
    *,
    title: str,
    company: str = "Test Company",
    location: str = "Mumbai",
    overall_score: float = 70.0,
    shortlist_likelihood_score: float | None = 70.0,
    data_quality_score: float | None = 80.0,
    remote: bool = False,
    work_mode: str = "",
    job_bucket: str = "",
    company_tier: str = "",
    freshness_bucket: str = "",
    posting_priority: int = 0,
) -> SimpleNamespace:
    """
    Create a minimal Job-compatible object.

    The selector only needs attribute access. Using a lightweight object here
    means this validation does not require API calls, Gemini, Google Sheets,
    or the complete production pipeline.
    """

    return SimpleNamespace(
        title=title,
        company=company,
        location=location,
        overall_score=overall_score,
        shortlist_likelihood_score=shortlist_likelihood_score,
        data_quality_score=data_quality_score,
        remote=remote,
        work_mode=work_mode,
        job_bucket=job_bucket,
        company_tier=company_tier,
        freshness_bucket=freshness_bucket,
        posting_priority=posting_priority,
        final_selection_eligible=False,
        final_selection_bucket="Rejected",
        final_selection_priority=0,
        final_selection_reason="",
        apply_priority=0,
    )


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def test_incompatible_role_is_rejected(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Freelance Copywriter",
        overall_score=90.0,
    )

    selected = selector.select([job])

    require(
        selected == [],
        "Copywriter must never enter the final queue.",
    )

    require(
        job.final_selection_eligible is False,
        "Copywriter must be marked ineligible.",
    )

    require(
        "incompatible role family" in job.final_selection_reason.lower(),
        (
            "Copywriter rejection reason must identify the incompatible "
            "role family."
        ),
    )


def test_service_desk_is_rejected(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Tier III Service Desk Engineer",
        overall_score=95.0,
    )

    selected = selector.select([job])

    require(
        selected == [],
        "Service Desk jobs must never enter the final queue.",
    )

    require(
        job.final_selection_eligible is False,
        "Service Desk job must be marked ineligible.",
    )


def test_wrong_location_is_rejected(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Data Analyst",
        location="Singapore",
        overall_score=95.0,
    )

    selected = selector.select([job])

    require(
        selected == [],
        "Singapore job must be rejected.",
    )

    require(
        job.final_selection_eligible is False,
        "Wrong-location job must be marked ineligible.",
    )

    require(
        "outside the target geography"
        in job.final_selection_reason.lower(),
        "Wrong-location rejection reason is incorrect.",
    )


def test_remote_target_role_is_eligible(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Senior Analytics Engineer",
        location="Remote",
        overall_score=70.0,
        shortlist_likelihood_score=55.0,
        remote=True,
    )

    selected = selector.select([job])

    require(
        len(selected) == 1,
        "Eligible remote analytics role must enter the final queue.",
    )

    require(
        job.final_selection_eligible is True,
        "Eligible remote job must be marked eligible.",
    )

    require(
        job.final_selection_bucket == "C - Review",
        (
            "A 70-score candidate without strong shortlist evidence "
            "should be classified as C - Review."
        ),
    )


def test_review_floor_allows_valid_lower_score(
    selector: FinalSelectionEngine,
) -> None:
    """
    This is the production blocker regression test.

    The previous selector required overall_score >= 65.

    A legitimate target-role candidate with score 53.05 therefore could
    never reach the final queue.

    The new selector intentionally allows >= 50 for C - Review.
    """

    job = make_job(
        title="Senior Analytics Engineer",
        company="Coinbase",
        location="Remote",
        overall_score=53.05,
        shortlist_likelihood_score=53.05,
        remote=True,
    )

    selected = selector.select([job])

    require(
        len(selected) == 1,
        (
            "A valid target-role remote candidate with score 53.05 "
            "should enter the review queue."
        ),
    )

    require(
        job.final_selection_eligible is True,
        "53.05 candidate should be final-selection eligible.",
    )

    require(
        job.final_selection_bucket == "C - Review",
        "53.05 candidate should be C - Review.",
    )

    require(
        job.final_selection_priority == 1,
        "53.05 candidate should receive review priority 1.",
    )


def test_score_below_floor_is_rejected(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Data Analyst",
        location="Mumbai",
        overall_score=49.99,
        shortlist_likelihood_score=80.0,
    )

    selected = selector.select([job])

    require(
        selected == [],
        "Scores below 50 must not enter the final queue.",
    )

    require(
        job.final_selection_eligible is False,
        "Below-floor job must be marked ineligible.",
    )

    require(
        "below the final-review floor"
        in job.final_selection_reason.lower(),
        "Below-floor rejection reason is incorrect.",
    )


def test_shortlist_score_is_not_a_hard_gate(
    selector: FinalSelectionEngine,
) -> None:
    """
    Regression test for the previous failure mode.

    A valid candidate should not be rejected merely because the secondary
    shortlist score is below 60 when the canonical overall score is strong
    enough for review.
    """

    job = make_job(
        title="Data Analyst",
        location="Mumbai",
        overall_score=70.0,
        shortlist_likelihood_score=40.0,
    )

    selected = selector.select([job])

    require(
        len(selected) == 1,
        (
            "Shortlist score must not independently reject a candidate "
            "that passes the canonical overall-score floor."
        ),
    )

    require(
        job.final_selection_eligible is True,
        "Candidate should remain eligible.",
    )


def test_strong_match_bucket(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Senior Data Analyst",
        location="Bengaluru",
        overall_score=78.0,
        shortlist_likelihood_score=68.0,
    )

    selected = selector.select([job])

    require(
        len(selected) == 1,
        "Strong candidate must be selected.",
    )

    require(
        job.final_selection_bucket == "B - Strong Match",
        (
            f"Expected B - Strong Match, got "
            f"{job.final_selection_bucket!r}."
        ),
    )

    require(
        job.final_selection_priority == 2,
        "Strong candidate should have priority 2.",
    )


def test_apply_now_bucket(
    selector: FinalSelectionEngine,
) -> None:
    job = make_job(
        title="Senior Analytics Engineer",
        location="Hyderabad",
        overall_score=90.0,
        shortlist_likelihood_score=85.0,
    )

    selected = selector.select([job])

    require(
        len(selected) == 1,
        "High-quality candidate must be selected.",
    )

    require(
        job.final_selection_bucket == "A - Apply Now",
        (
            f"Expected A - Apply Now, got "
            f"{job.final_selection_bucket!r}."
        ),
    )

    require(
        job.final_selection_priority == 3,
        "Apply-now candidate should have priority 3.",
    )


def test_sorting(
    selector: FinalSelectionEngine,
) -> None:
    review_job = make_job(
        title="Data Analyst",
        company="ReviewCo",
        location="Mumbai",
        overall_score=55.0,
        shortlist_likelihood_score=55.0,
    )

    strong_job = make_job(
        title="Senior Data Analyst",
        company="StrongCo",
        location="Bengaluru",
        overall_score=78.0,
        shortlist_likelihood_score=70.0,
    )

    apply_job = make_job(
        title="Analytics Engineer",
        company="ApplyCo",
        location="Hyderabad",
        overall_score=90.0,
        shortlist_likelihood_score=85.0,
    )

    selected = selector.select(
        [
            review_job,
            apply_job,
            strong_job,
        ]
    )

    require(
        len(selected) == 3,
        "All three valid candidates should be selected.",
    )

    require(
        selected[0].company == "ApplyCo",
        "Priority-3 candidate must rank first.",
    )

    require(
        selected[1].company == "StrongCo",
        "Priority-2 candidate must rank second.",
    )

    require(
        selected[2].company == "ReviewCo",
        "Priority-1 candidate must rank third.",
    )


def test_mixed_production_like_candidate_set(
    selector: FinalSelectionEngine,
) -> None:
    """
    Simulates the shape of the latest production failure.

    Expected:

        valid target geography / role candidates -> selected
        incompatible roles                    -> rejected
        wrong geography                       -> rejected
        low-score valid candidates             -> rejected
    """

    jobs = [
        make_job(
            title="Monetization Operations Analyst",
            company="Stripe",
            location="Bengaluru",
            overall_score=57.75,
            shortlist_likelihood_score=57.75,
        ),
        make_job(
            title="Risk Operations Analyst",
            company="Stripe",
            location="Remote",
            overall_score=55.30,
            shortlist_likelihood_score=55.30,
            remote=True,
        ),
        make_job(
            title="Senior Analytics Engineer, GFCO Analytics",
            company="Coinbase",
            location="Remote",
            overall_score=53.05,
            shortlist_likelihood_score=53.05,
            remote=True,
        ),
        make_job(
            title="Data Analyst",
            company="Stripe",
            location="New York",
            overall_score=95.0,
        ),
        make_job(
            title="Tier III Service Desk Engineer",
            company="Unio Digital",
            location="Worldwide",
            overall_score=95.0,
        ),
        make_job(
            title="Freelance Copywriter",
            company="Coalition Technologies",
            location="Worldwide",
            overall_score=95.0,
        ),
    ]

    selected = selector.select(jobs)

    selected_companies = {
        job.company
        for job in selected
    }

    require(
        selected_companies == {"Stripe", "Coinbase"},
        (
            "Production-like candidate set should retain only valid "
            f"target-role/location candidates. Got {selected_companies!r}."
        ),
    )

    require(
        len(selected) == 3,
        (
            "Expected the three valid target candidates to enter the "
            f"final queue; got {len(selected)}."
        ),
    )

    for job in selected:
        require(
            job.final_selection_eligible is True,
            f"{job.title} should be eligible.",
        )


def main() -> int:
    print("=" * 80)
    print("FINAL SELECTION ENGINE VALIDATION")
    print("=" * 80)

    selector = FinalSelectionEngine()

    tests = [
        (
            "incompatible role rejection",
            test_incompatible_role_is_rejected,
        ),
        (
            "service desk rejection",
            test_service_desk_is_rejected,
        ),
        (
            "wrong location rejection",
            test_wrong_location_is_rejected,
        ),
        (
            "remote target-role eligibility",
            test_remote_target_role_is_eligible,
        ),
        (
            "review floor regression",
            test_review_floor_allows_valid_lower_score,
        ),
        (
            "below-floor rejection",
            test_score_below_floor_is_rejected,
        ),
        (
            "shortlist score is advisory",
            test_shortlist_score_is_not_a_hard_gate,
        ),
        (
            "strong match bucket",
            test_strong_match_bucket,
        ),
        (
            "apply-now bucket",
            test_apply_now_bucket,
        ),
        (
            "priority sorting",
            test_sorting,
        ),
        (
            "production-like candidate set",
            test_mixed_production_like_candidate_set,
        ),
    ]

    passed = 0

    for name, test in tests:
        try:
            test(selector)
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}")
            return 1

        print(f"[PASS] {name}")
        passed += 1

    print()
    print("=" * 80)
    print(
        f"FINAL SELECTION VALIDATION PASSED: "
        f"{passed}/{len(tests)} tests"
    )
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())