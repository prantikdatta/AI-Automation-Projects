from __future__ import annotations

import logging
from typing import Iterable

from job_search_automation.intelligence.eligibility import (
    JobEligibilityEngine,
)
from job_search_automation.models.job import Job


LOGGER = logging.getLogger("job_search_automation")


class FinalSelectionEngine:
    """
    Final deterministic application-selection engine.

    Pipeline position:

        Evaluated Jobs
             ↓
        Hard Eligibility
             ↓
        Overall Score Gate
             ↓
        Selection Bucket
             ↓
        Application Priority
             ↓
        Final Application Queue

    Responsibilities
    ----------------
    This engine:

        - applies hard role eligibility
        - applies hard location eligibility
        - applies the canonical overall-score floor
        - classifies eligible jobs
        - assigns application priority
        - records an explicit selection reason
        - sorts the final application queue

    This engine does NOT:

        - search providers
        - deduplicate jobs
        - perform freshness filtering
        - call Gemini
        - perform resume matching
        - calculate the underlying score
        - export to Google Sheets

    Important scoring rule
    ----------------------
    `overall_score` is the canonical score.

    `shortlist_likelihood_score` is retained as a secondary signal for
    backward compatibility and ranking, but it is NOT a hard eligibility gate.

    This prevents a duplicate scoring contract where one score can reject a
    job even though the canonical score considers it viable.
    """

    # ==========================================================
    # FINAL SELECTION FLOOR
    # ==========================================================

    MIN_REVIEW_SCORE = 50.0

    # ==========================================================
    # OPTIONAL DATA QUALITY FLOOR
    # ==========================================================

    MIN_DATA_QUALITY_SCORE = 50.0

    # ==========================================================
    # BUCKET THRESHOLDS
    # ==========================================================

    HIGH_SCORE = 75.0
    HIGH_SHORTLIST = 75.0

    MEDIUM_SCORE = 65.0

    # ==========================================================
    # PRIORITY THRESHOLDS
    # ==========================================================

    HIGH_PRIORITY_SCORE = 85.0
    HIGH_PRIORITY_SHORTLIST = 80.0

    MEDIUM_PRIORITY_SCORE = 75.0
    MEDIUM_PRIORITY_SHORTLIST = 65.0

    # ==========================================================
    # CONSTRUCTOR
    # ==========================================================

    def __init__(self) -> None:
        self.eligibility = JobEligibilityEngine()

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def select(
        self,
        jobs: Iterable[Job],
    ) -> list[Job]:
        """
        Select jobs that are eligible for the final application queue.

        Jobs that fail hard eligibility or the minimum review score remain
        rejected and receive explicit metadata explaining why.

        Returns
        -------
        list[Job]
            Eligible jobs sorted by application priority and score.
        """

        jobs_list = list(jobs)
        selected: list[Job] = []

        LOGGER.info("")
        LOGGER.info("=" * 80)
        LOGGER.info("FINAL SELECTION ENGINE")
        LOGGER.info("=" * 80)
        LOGGER.info(
            "Candidates received : %d",
            len(jobs_list),
        )

        for job in jobs_list:
            self._evaluate_job(job)

            if job.final_selection_eligible:
                selected.append(job)

        selected.sort(
            key=self._selection_sort_key,
            reverse=True,
        )

        LOGGER.info(
            "Final application queue : %d",
            len(selected),
        )

        LOGGER.info(
            "Selection buckets : %s",
            self._bucket_counts(selected),
        )

        LOGGER.info("=" * 80)

        return selected

    def evaluate(
        self,
        job: Job,
    ) -> Job:
        """
        Public single-job evaluation API.
        """

        self._evaluate_job(job)

        return job

    # ==========================================================
    # SINGLE JOB EVALUATION
    # ==========================================================

    def _evaluate_job(
        self,
        job: Job,
    ) -> None:
        """
        Apply hard eligibility and final-selection quality rules.
        """

        self._reset_selection_state(job)

        # ------------------------------------------------------
        # STEP 1 — HARD ROLE + LOCATION ELIGIBILITY
        # ------------------------------------------------------

        eligible, eligibility_reason = (
            self.eligibility.evaluate(job)
        )

        if not eligible:
            job.final_selection_reason = eligibility_reason

            LOGGER.info(
                "FINAL REJECT | %s | %s | reason=%s",
                job.company,
                job.title,
                eligibility_reason,
            )

            return

        # ------------------------------------------------------
        # STEP 2 — SCORE NORMALIZATION
        # ------------------------------------------------------

        overall_score = self._score(
            getattr(job, "overall_score", None),
        )

        shortlist_score = self._score(
            getattr(
                job,
                "shortlist_likelihood_score",
                None,
            ),
        )

        data_quality_score = self._score(
            getattr(
                job,
                "data_quality_score",
                None,
            ),
        )

        # ------------------------------------------------------
        # STEP 3 — CANONICAL SCORE GATE
        # ------------------------------------------------------

        if overall_score is None:
            job.final_selection_reason = (
                "Rejected: missing canonical overall score."
            )

            LOGGER.info(
                "FINAL REJECT | %s | %s | reason=missing overall score",
                job.company,
                job.title,
            )

            return

        if overall_score < self.MIN_REVIEW_SCORE:
            job.final_selection_reason = (
                f"Rejected: overall score "
                f"{overall_score:.2f} is below the final-review "
                f"floor of {self.MIN_REVIEW_SCORE:.0f}."
            )

            LOGGER.info(
                "FINAL REJECT | %s | %s | score=%.2f | reason=below review floor",
                job.company,
                job.title,
                overall_score,
            )

            return

        # ------------------------------------------------------
        # STEP 4 — OPTIONAL DATA QUALITY GATE
        # ------------------------------------------------------

        if (
            data_quality_score is not None
            and data_quality_score < self.MIN_DATA_QUALITY_SCORE
        ):
            job.final_selection_reason = (
                f"Rejected: data quality score "
                f"{data_quality_score:.2f} is below "
                f"{self.MIN_DATA_QUALITY_SCORE:.0f}."
            )

            LOGGER.info(
                "FINAL REJECT | %s | %s | score=%.2f | data_quality=%.2f",
                job.company,
                job.title,
                overall_score,
                data_quality_score,
            )

            return

        # ------------------------------------------------------
        # STEP 5 — ELIGIBLE
        # ------------------------------------------------------

        job.final_selection_eligible = True

        job.final_selection_bucket = (
            self._determine_bucket(
                overall_score=overall_score,
                shortlist_score=shortlist_score,
            )
        )

        job.final_selection_priority = (
            self._determine_priority(
                overall_score=overall_score,
                shortlist_score=shortlist_score,
                bucket=job.final_selection_bucket,
            )
        )

        job.final_selection_reason = (
            self._build_reason(
                job=job,
                overall_score=overall_score,
                shortlist_score=shortlist_score,
                eligibility_reason=eligibility_reason,
            )
        )

        job.apply_priority = job.final_selection_priority

        LOGGER.info(
            "FINAL SELECT | %s | %s | location=%s | "
            "score=%.2f | shortlist=%s | bucket=%s | priority=%d",
            job.company,
            job.title,
            job.location,
            overall_score,
            (
                f"{shortlist_score:.2f}"
                if shortlist_score is not None
                else "N/A"
            ),
            job.final_selection_bucket,
            job.final_selection_priority,
        )

    # ==========================================================
    # RESET
    # ==========================================================

    @staticmethod
    def _reset_selection_state(
        job: Job,
    ) -> None:
        """
        Reset all final-selection metadata before evaluation.
        """

        job.final_selection_eligible = False
        job.final_selection_bucket = "Rejected"
        job.final_selection_priority = 0
        job.final_selection_reason = ""

    # ==========================================================
    # BUCKET
    # ==========================================================

    def _determine_bucket(
        self,
        *,
        overall_score: float | None,
        shortlist_score: float | None,
    ) -> str:
        """
        Classify an eligible job.

        A — Apply Now
            Very strong canonical score and strong shortlist signal.

        B — Strong Match
            Strong canonical score.

        C — Review
            Passed hard eligibility and minimum score floor, but requires
            human review before application.
        """

        score = overall_score or 0.0
        shortlist = shortlist_score or 0.0

        if (
            score >= self.HIGH_SCORE
            and shortlist >= self.HIGH_SHORTLIST
        ):
            return "A - Apply Now"

        if score >= self.MEDIUM_SCORE:
            return "B - Strong Match"

        return "C - Review"

    # ==========================================================
    # APPLICATION PRIORITY
    # ==========================================================

    @staticmethod
    def _determine_priority(
        *,
        overall_score: float | None,
        shortlist_score: float | None,
        bucket: str,
    ) -> int:
        """
        Assign final application priority.

        Priority contract
        -----------------
            2 = Apply Now
            1 = Strong Match / Review
            0 = Rejected

        Bucket classification and application priority are intentionally
        separate concepts.

        A - Apply Now:
            Highest actionable priority.

        B - Strong Match:
            Eligible and relevant, but below Apply Now.

        C - Review:
            Eligible but requires human review.

        The final-selection tests and downstream application queue use
        this two-level actionable priority model.
        """

        if bucket == "A - Apply Now":
            return 2

        if bucket in {
            "B - Strong Match",
            "C - Review",
        }:
            return 1

        return 0

    # ==========================================================
    # REASON
    # ==========================================================

    @staticmethod
    def _build_reason(
        *,
        job: Job,
        overall_score: float | None,
        shortlist_score: float | None,
        eligibility_reason: str,
    ) -> str:
        """
        Build a persisted explanation for the final-selection decision.
        """

        parts: list[str] = [
            eligibility_reason,
        ]

        if overall_score is not None:
            parts.append(
                f"overall score {overall_score:.1f}"
            )

        if shortlist_score is not None:
            parts.append(
                f"shortlist likelihood {shortlist_score:.1f}"
            )

        company_tier = getattr(
            job,
            "company_tier",
            None,
        )

        if company_tier:
            parts.append(
                f"company tier {company_tier}"
            )

        job_bucket = getattr(
            job,
            "job_bucket",
            None,
        )

        if job_bucket:
            parts.append(
                f"job bucket {job_bucket}"
            )

        freshness_bucket = getattr(
            job,
            "freshness_bucket",
            None,
        )

        if freshness_bucket:
            parts.append(
                f"freshness {freshness_bucket}"
            )

        return (
            "Passed final application criteria: "
            + "; ".join(parts)
            + "."
        )

    # ==========================================================
    # SORTING
    # ==========================================================

    @staticmethod
    def _selection_sort_key(
        job: Job,
    ) -> tuple[float, float, float, float]:
        """
        Sort final candidates by:

            1. Application priority
            2. Canonical overall score
            3. Secondary shortlist score
            4. Posting priority

        `overall_score` remains the primary quality metric.
        """

        return (
            float(
                getattr(
                    job,
                    "final_selection_priority",
                    0,
                )
                or 0
            ),
            float(
                getattr(
                    job,
                    "overall_score",
                    0.0,
                )
                or 0.0
            ),
            float(
                getattr(
                    job,
                    "shortlist_likelihood_score",
                    0.0,
                )
                or 0.0
            ),
            float(
                getattr(
                    job,
                    "posting_priority",
                    0,
                )
                or 0
            ),
        )

    # ==========================================================
    # SCORE NORMALIZATION
    # ==========================================================

    @staticmethod
    def _score(
        value: float | int | str | None,
    ) -> float | None:
        """
        Normalize a score to the 0–100 range.

        Invalid values become None rather than silently becoming zero.
        """

        if value is None:
            return None

        try:
            score = float(value)
        except (TypeError, ValueError):
            return None

        if score != score:
            return None

        if score == float("inf") or score == float("-inf"):
            return None

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    # ==========================================================
    # BUCKET COUNTS
    # ==========================================================

    @staticmethod
    def _bucket_counts(
        jobs: Iterable[Job],
    ) -> dict[str, int]:
        """
        Return selection-bucket counts for production diagnostics.
        """

        counts: dict[str, int] = {}

        for job in jobs:
            bucket = str(
                getattr(
                    job,
                    "final_selection_bucket",
                    "Unknown",
                )
            )

            counts[bucket] = (
                counts.get(bucket, 0) + 1
            )

        return counts