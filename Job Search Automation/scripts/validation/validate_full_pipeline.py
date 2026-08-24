from __future__ import annotations

"""
Production end-to-end validation for the real SearchPipeline.

This validator executes the actual production path:

SearchStrategyEngine
    ↓
SearchOrchestrator
    ↓
ProviderRouter / ProviderManager
    ↓
API + ATS providers
    ↓
Canonical Jobs
    ↓
Deduplication
    ↓
Freshness
    ↓
ResumeMatcher
    ↓
Deterministic Score
    ↓
Ranking
    ↓
Final Selection
    ↓
Google Sheets mapping

The real Google Sheets write is intercepted so validation does not create
duplicate production rows.

No provider is mocked.
No SearchPipeline stage is mocked.
No production scoring is mocked.
"""

import math
import sys
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Repository import setup
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from job_search_automation.models.job import Job
from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


# ---------------------------------------------------------------------------
# Validation state
# ---------------------------------------------------------------------------

class ValidationState:
    def __init__(self) -> None:
        self.collected = 0
        self.enriched = 0
        self.evaluated = 0
        self.selected = 0
        self.exported = 0

        self.headers: list[Any] = []
        self.rows: list[Any] = []

        self.providers: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def wrap_method(
    obj: Any,
    name: str,
    after: Callable[..., None],
) -> None:
    """
    Wrap one production method while preserving its real implementation.
    """

    original = getattr(obj, name)

    def wrapped(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = original(
            *args,
            **kwargs,
        )

        after(
            result,
            *args,
            **kwargs,
        )

        return result

    setattr(
        obj,
        name,
        wrapped,
    )


# ---------------------------------------------------------------------------
# Job validation
# ---------------------------------------------------------------------------

def validate_job(
    job: Job,
    index: int,
) -> None:
    """
    Validate the canonical Job contract after final selection.
    """

    require(
        isinstance(job, Job),
        f"Job #{index} is not a Job model.",
    )

    require(
        bool(job.title.strip()),
        f"Job #{index} has no title.",
    )

    require(
        bool(job.company.strip()),
        f"Job #{index} has no company.",
    )

    require(
        bool(job.location.strip()),
        f"Job #{index} has no location.",
    )

    require(
        bool(job.job_url.strip()),
        f"Job #{index} has no job_url.",
    )

    require(
        bool(job.provider.strip()),
        f"Job #{index} has no provider.",
    )

    # ------------------------------------------------------
    # Deterministic score
    # ------------------------------------------------------

    require(
        job.overall_score is not None,
        f"Job #{index} has no overall_score.",
    )

    score = float(job.overall_score)

    require(
        math.isfinite(score),
        f"Job #{index} has non-finite overall_score.",
    )

    require(
        0.0 <= score <= 100.0,
        (
            f"Job #{index} has invalid overall_score="
            f"{score}."
        ),
    )

    # ------------------------------------------------------
    # Score synchronization
    # ------------------------------------------------------

    if job.shortlist_likelihood_score is not None:
        require(
            math.isclose(
                float(job.shortlist_likelihood_score),
                score,
                abs_tol=0.01,
            ),
            (
                f"Job #{index} has conflicting deterministic scores: "
                f"overall_score={score}, "
                f"shortlist_likelihood_score="
                f"{job.shortlist_likelihood_score}."
            ),
        )

    # ------------------------------------------------------
    # Resume matching
    # ------------------------------------------------------

    require(
        job.resume_match_result is not None,
        f"Job #{index} has no resume_match_result.",
    )

    # ------------------------------------------------------
    # Final selection
    # ------------------------------------------------------

    require(
        job.final_selection_eligible is True,
        (
            f"Selected job #{index} is not marked eligible: "
            f"{job.final_selection_eligible!r}."
        ),
    )

    require(
        job.final_selection_bucket not in (
            None,
            "",
            "Reject",
        ),
        (
            f"Selected job #{index} has invalid "
            f"final_selection_bucket="
            f"{job.final_selection_bucket!r}."
        ),
    )

    require(
        job.final_selection_priority > 0,
        (
            f"Selected job #{index} has invalid "
            f"final_selection_priority="
            f"{job.final_selection_priority}."
        ),
    )


# ---------------------------------------------------------------------------
# Ranking validation
# ---------------------------------------------------------------------------

def validate_ranking(
    jobs: list[Job],
) -> None:
    """
    Final jobs must be ordered by deterministic score descending.

    Posting priority is the tie-break.
    """

    scores = [
        float(job.overall_score)
        for job in jobs
    ]

    require(
        scores == sorted(
            scores,
            reverse=True,
        ),
        (
            "Final jobs are not ranked by descending "
            f"overall_score: {scores}."
        ),
    )

    for previous, current in zip(
        jobs,
        jobs[1:],
    ):
        previous_score = float(
            previous.overall_score,
        )

        current_score = float(
            current.overall_score,
        )

        if previous_score == current_score:
            previous_priority = (
                previous.posting_priority or 0
            )

            current_priority = (
                current.posting_priority or 0
            )

            require(
                previous_priority >= current_priority,
                (
                    "Tie-break ranking violation: equal-score jobs "
                    "are not ordered by posting_priority."
                ),
            )


# ---------------------------------------------------------------------------
# Deduplication validation
# ---------------------------------------------------------------------------

def validate_deduplication(
    jobs: list[Job],
) -> None:
    """
    No duplicate canonical job URLs may remain in final output.
    """

    urls = [
        job.job_url.strip().lower().rstrip("/")
        for job in jobs
        if job.job_url
    ]

    require(
        len(urls) == len(set(urls)),
        "Duplicate job URLs remain in final output.",
    )


# ---------------------------------------------------------------------------
# Final selection validation
# ---------------------------------------------------------------------------

def validate_final_selection(
    jobs: list[Job],
) -> None:
    """
    Validate final-selection metadata against the production
    FinalSelectionEngine contract.
    """

    for job in jobs:
        require(
            job.final_selection_eligible is True,
            (
                f"Final output contains an ineligible job: "
                f"{job.title}."
            ),
        )

        require(
            job.final_selection_bucket in {
                "A - Apply Now",
                "B - Strong Match",
                "C - Review",
            },
            (
                f"Invalid final-selection bucket for "
                f"{job.title}: "
                f"{job.final_selection_bucket!r}."
            ),
        )

        require(
            job.final_selection_priority in {
                1,
                2,
                3,
            },
            (
                f"Invalid final-selection priority for "
                f"{job.title}: "
                f"{job.final_selection_priority!r}."
            ),
        )


# ---------------------------------------------------------------------------
# Sheets validation
# ---------------------------------------------------------------------------

def validate_sheets_mapping(
    state: ValidationState,
    jobs: list[Job],
) -> None:
    """
    Validate the real Google Sheets mapping without writing to Sheets.
    """

    require(
        bool(state.headers),
        "Google Sheets export headers are empty.",
    )

    require(
        len(state.headers) == 17,
        (
            "Google Sheets export must contain exactly "
            f"17 headers; found {len(state.headers)}."
        ),
    )

    require(
        len(state.rows) == len(jobs),
        (
            "Google Sheets row count does not match final "
            f"job count: rows={len(state.rows)}, "
            f"jobs={len(jobs)}."
        ),
    )

    for index, row in enumerate(
        state.rows,
        start=1,
    ):
        require(
            len(row) == len(state.headers),
            (
                f"Google Sheets row #{index} has "
                f"{len(row)} columns but expected "
                f"{len(state.headers)}."
            ),
        )


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 90)
    print("STARTING REAL PRODUCTION PIPELINE VALIDATION")
    print("=" * 90)
    print()

    state = ValidationState()

    pipeline = SearchPipeline()

    # ------------------------------------------------------
    # Capture production stage counts
    # ------------------------------------------------------

    def after_collect(
        jobs: list[Job],
        *_: Any,
        **__: Any,
    ) -> None:
        state.collected = len(jobs)

        for job in jobs:
            provider = (
                job.provider
                or job.source
                or "Unknown"
            )

            state.providers[provider] = (
                state.providers.get(
                    provider,
                    0,
                )
                + 1
            )

    def after_enrich(
        job: Job,
        *_: Any,
        **__: Any,
    ) -> None:
        state.enriched += 1

    def after_evaluate(
        result: Any,
        *_: Any,
        **__: Any,
    ) -> None:
        state.evaluated += 1

    def after_select(
        jobs: list[Job],
        *_: Any,
        **__: Any,
    ) -> None:
        state.selected = len(jobs)

    wrap_method(
        pipeline.search_orchestrator,
        "collect_jobs",
        after_collect,
    )

    wrap_method(
        pipeline.enrichment_pipeline,
        "process",
        after_enrich,
    )

    wrap_method(
        pipeline.resume_matcher,
        "evaluate",
        after_evaluate,
    )

    wrap_method(
        pipeline.final_selector,
        "select",
        after_select,
    )

    # ------------------------------------------------------
    # Capture Sheets export
    # ------------------------------------------------------

    def capture_sheet_export(
        *,
        headers: Any,
        rows: Any,
    ) -> None:
        state.headers = list(
            headers or [],
        )

        state.rows = list(
            rows or [],
        )

        state.exported = len(
            state.rows,
        )

        print(
            f"[VALIDATION] Sheets export captured: "
            f"{state.exported} rows"
        )

    pipeline.google_sheets.append_jobs = (
        capture_sheet_export
    )

    # ------------------------------------------------------
    # Execute REAL pipeline
    # ------------------------------------------------------

    response = pipeline.run()

    # ------------------------------------------------------
    # Response contract
    # ------------------------------------------------------

    require(
        isinstance(
            response,
            SearchResponse,
        ),
        (
            "SearchPipeline must return SearchResponse; "
            f"got {type(response).__name__}."
        ),
    )

    require(
        response.success is True,
        (
            f"SearchPipeline returned success="
            f"{response.success!r}."
        ),
    )

    jobs = response.jobs

    # ------------------------------------------------------
    # Stage invariants
    # ------------------------------------------------------

    require(
        state.collected > 0,
        "BLOCKER: zero jobs collected by real search stack.",
    )

    require(
        state.enriched > 0,
        "BLOCKER: zero jobs reached enrichment.",
    )

    require(
        state.evaluated > 0,
        "BLOCKER: zero jobs reached ResumeMatcher.",
    )

    require(
        state.selected > 0,
        "BLOCKER: zero jobs survived final selection.",
    )

    require(
        state.exported == state.selected,
        (
            "Google Sheets export count does not match "
            f"selected count: exported={state.exported}, "
            f"selected={state.selected}."
        ),
    )

    require(
        len(jobs) == state.selected,
        (
            "SearchResponse job count does not match "
            f"selected count: response={len(jobs)}, "
            f"selected={state.selected}."
        ),
    )

    require(
        response.total_found == state.selected,
        (
            "SearchResponse.total_found does not match "
            f"selected count: total_found={response.total_found}, "
            f"selected={state.selected}."
        ),
    )

    require(
        response.total_returned == state.selected,
        (
            "SearchResponse.total_returned does not match "
            f"selected count: total_returned={response.total_returned}, "
            f"selected={state.selected}."
        ),
    )

    # ------------------------------------------------------
    # Job-level invariants
    # ------------------------------------------------------

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        validate_job(
            job,
            index,
        )

    # ------------------------------------------------------
    # Pipeline invariants
    # ------------------------------------------------------

    validate_ranking(jobs)

    validate_deduplication(jobs)

    validate_final_selection(jobs)

    validate_sheets_mapping(
        state,
        jobs,
    )

    # ------------------------------------------------------
    # Report
    # ------------------------------------------------------

    print()
    print("=" * 90)
    print("VALIDATION SUMMARY")
    print("=" * 90)

    print(
        f"Collected jobs      : {state.collected}"
    )

    print(
        f"Enriched jobs       : {state.enriched}"
    )

    print(
        f"Evaluated jobs      : {state.evaluated}"
    )

    print(
        f"Selected jobs       : {state.selected}"
    )

    print(
        f"Sheets rows         : {state.exported}"
    )

    print(
        f"Sheets headers      : {len(state.headers)}"
    )

    print(
        f"SearchResponse jobs : {len(jobs)}"
    )

    print()
    print("Provider contribution:")

    for provider, count in sorted(
        state.providers.items(),
    ):
        print(
            f"  {provider:25s}: {count}"
        )

    print()
    print("Final jobs:")

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        print(
            f"  {index:03d} | "
            f"{job.title[:45]:45s} | "
            f"{job.company[:25]:25s} | "
            f"{job.location[:20]:20s} | "
            f"score={float(job.overall_score):6.2f} | "
            f"{job.final_selection_bucket:12s} | "
            f"priority={job.final_selection_priority}"
        )

    print()
    print("[PASS] Real SearchPipeline executed.")
    print("[PASS] Real provider/search stack executed.")
    print("[PASS] Real enrichment executed.")
    print("[PASS] Real ResumeMatcher executed.")
    print("[PASS] Deterministic score persisted to Job.overall_score.")
    print("[PASS] Final selection executed.")
    print("[PASS] Final jobs are role/location eligible.")
    print("[PASS] Final jobs are ranked by deterministic score.")
    print("[PASS] Final output is deduplicated.")
    print("[PASS] SearchResponse contract is valid.")
    print("[PASS] Google Sheets mapping validated without writing.")
    print()
    print("=" * 90)
    print("PRODUCTION END-TO-END PIPELINE VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    main()