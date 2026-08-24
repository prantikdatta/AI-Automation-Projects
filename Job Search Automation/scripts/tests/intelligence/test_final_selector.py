from __future__ import annotations

import re
from dataclasses import dataclass

from job_search_automation.models.job import Job


@dataclass(frozen=True)
class SelectionDecision:
    """
    Deterministic final-selection decision for a job.
    """

    eligible: bool
    bucket: str
    reason: str
    priority: int


class FinalSelectionEngine:
    """
    Determines whether an evaluated job should enter the
    final application queue.

    This component is intentionally deterministic.

    Responsibilities
    ----------------
    - Validate target role-family relevance.
    - Validate target location / remote eligibility.
    - Apply minimum score thresholds.
    - Assign final application bucket.
    - Assign application priority.
    - Persist selection metadata on Job.

    This component does NOT:
    - search providers
    - call Gemini
    - enrich jobs
    - perform resume matching
    - deduplicate jobs
    - apply freshness rules
    - export to Google Sheets
    """

    # ==========================================================
    # TARGET ROLE FAMILIES
    # ==========================================================

    TARGET_ROLE_PATTERNS: tuple[str, ...] = (
        # ------------------------------------------------------
        # Data / Analytics
        # ------------------------------------------------------
        r"\bdata\s+analyst\b",
        r"\bsenior\s+data\s+analyst\b",
        r"\bstaff\s+data\s+analyst\b",
        r"\blead\s+data\s+analyst\b",
        r"\banalytics\s+engineer\b",
        r"\bsenior\s+analytics\s+engineer\b",
        r"\bstaff\s+analytics\s+engineer\b",
        r"\bdata\s+engineer\b",
        r"\breporting\s+analyst\b",
        r"\bbusiness\s+intelligence\s+analyst\b",
        r"\bbi\s+analyst\b",
        r"\bbi\s+developer\b",
        r"\bbusiness\s+intelligence\s+developer\b",
        r"\binsights\s+analyst\b",
        r"\bdecision\s+scientist\b",
        r"\banalytics\s+consultant\b",
        r"\bdata\s+consultant\b",

        # ------------------------------------------------------
        # Product / Strategy
        # ------------------------------------------------------
        r"\bproduct\s+analyst\b",
        r"\bproduct\s+analytics\b",
        r"\bstrategy\s+analytics\b",
        r"\bstrategy\s+and\s+analytics\b",
        r"\bstrategy\s+analyst\b",
        r"\bbusiness\s+analyst\b",

        # ------------------------------------------------------
        # Risk / Financial Analytics
        # ------------------------------------------------------
        r"\bcredit\s+risk\s+analyst\b",
        r"\bcredit\s+analyst\b",
        r"\brisk\s+analyst\b",
        r"\brisk\s+analytics\b",
        r"\bfinancial\s+analyst\b",
        r"\bfinance\s+analyst\b",
        r"\boperations\s+analyst\b",
        r"\bdata\s+risk\s+analyst\b",

        # ------------------------------------------------------
        # Program / Project / PMO
        # ------------------------------------------------------
        r"\bprogram\s+manager\b",
        r"\btechnical\s+program\s+manager\b",
        r"\bproject\s+manager\b",
        r"\bproject\s+management\b",
        r"\bdelivery\s+manager\b",
        r"\bprogram\s+management\b",
        r"\bpmo\b",
        r"\bpmo\s+analyst\b",
        r"\btransformation\s+manager\b",
        r"\bimplementation\s+manager\b",
        r"\boperations\s+manager\b",
        r"\btechnical\s+project\s+manager\b",
        r"\bprogram\s+analyst\b",
        r"\bproject\s+analyst\b",
    )

    # ==========================================================
    # TARGET LOCATIONS
    # ==========================================================

    TARGET_LOCATION_PATTERNS: tuple[str, ...] = (
        r"\bmumbai\b",
        r"\bnavi\s+mumbai\b",
        r"\bbangalore\b",
        r"\bbengaluru\b",
        r"\bhyderabad\b",
        r"\bgurugram\b",
        r"\bgurgaon\b",
        r"\bremote\s+india\b",
        r"\bindia\s+remote\b",
    )

    REMOTE_PATTERNS: tuple[str, ...] = (
        r"\bremote\b",
        r"\bremote\s+india\b",
        r"\bindia\s+remote\b",
        r"\bwork\s+from\s+home\b",
        r"\bwfh\b",
        r"\banywhere\b",
    )

    # ==========================================================
    # SCORE THRESHOLDS
    # ==========================================================

    APPLY_NOW_THRESHOLD = 75.0
    STRONG_MATCH_THRESHOLD = 65.0
    REVIEW_THRESHOLD = 55.0

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def select(
        self,
        jobs: list[Job],
    ) -> list[Job]:
        """
        Evaluate and return jobs eligible for the final
        application queue.

        Jobs failing hard eligibility gates are excluded.
        """

        selected: list[Job] = []

        for job in jobs:
            decision = self.evaluate(job)

            self._apply_decision(
                job,
                decision,
            )

            if decision.eligible:
                selected.append(job)

        return selected

    def evaluate(
        self,
        job: Job,
    ) -> SelectionDecision:
        """
        Evaluate a single job against final-selection rules.
        """

        title = self._normalize(job.title)

        location = self._normalize(job.location)

        # ------------------------------------------------------
        # GATE 1 - ROLE
        # ------------------------------------------------------

        if not self._is_target_role(title):
            return SelectionDecision(
                eligible=False,
                bucket="Reject",
                reason=(
                    "Rejected: role is outside the configured "
                    "target role families."
                ),
                priority=0,
            )

        # ------------------------------------------------------
        # GATE 2 - LOCATION
        # ------------------------------------------------------

        if not self._is_target_location(
            job=job,
            normalized_location=location,
        ):
            return SelectionDecision(
                eligible=False,
                bucket="Reject",
                reason=(
                    "Rejected: location is outside the configured "
                    "target locations and the role is not remote."
                ),
                priority=0,
            )

        # ------------------------------------------------------
        # GATE 3 - SCORE
        # ------------------------------------------------------

        score = self._score(job)

        if score < self.REVIEW_THRESHOLD:
            return SelectionDecision(
                eligible=False,
                bucket="Reject",
                reason=(
                    f"Rejected: final score {score:.2f} is below "
                    f"the minimum review threshold "
                    f"{self.REVIEW_THRESHOLD:.2f}."
                ),
                priority=0,
            )

        # ------------------------------------------------------
        # BUCKET 1 - APPLY NOW
        # ------------------------------------------------------

        if score >= self.APPLY_NOW_THRESHOLD:
            return SelectionDecision(
                eligible=True,
                bucket="Apply Now",
                reason=(
                    f"Eligible: score {score:.2f} meets the "
                    f"Apply Now threshold."
                ),
                priority=100,
            )

        # ------------------------------------------------------
        # BUCKET 2 - STRONG MATCH
        # ------------------------------------------------------

        if score >= self.STRONG_MATCH_THRESHOLD:
            return SelectionDecision(
                eligible=True,
                bucket="Strong Match",
                reason=(
                    f"Eligible: score {score:.2f} meets the "
                    f"Strong Match threshold."
                ),
                priority=80,
            )

        # ------------------------------------------------------
        # BUCKET 3 - REVIEW
        # ------------------------------------------------------

        return SelectionDecision(
            eligible=True,
            bucket="Review",
            reason=(
                f"Eligible for manual review with score "
                f"{score:.2f}."
            ),
            priority=60,
        )

    # ==========================================================
    # ROLE ELIGIBILITY
    # ==========================================================

    @classmethod
    def _is_target_role(
        cls,
        title: str,
    ) -> bool:
        """
        Return True when the title belongs to one of the
        configured target role families.
        """

        return any(
            re.search(
                pattern,
                title,
                flags=re.IGNORECASE,
            )
            for pattern in cls.TARGET_ROLE_PATTERNS
        )

    # ==========================================================
    # LOCATION ELIGIBILITY
    # ==========================================================

    @classmethod
    def _is_target_location(
        cls,
        job: Job,
        normalized_location: str,
    ) -> bool:
        """
        Return True when the job is remote or located in one
        of the configured target locations.
        """

        # Explicit canonical remote flag.
        if job.remote:
            return True

        # Remote indicated by location text.
        if any(
            re.search(
                pattern,
                normalized_location,
                flags=re.IGNORECASE,
            )
            for pattern in cls.REMOTE_PATTERNS
        ):
            return True

        # Preferred physical locations.
        return any(
            re.search(
                pattern,
                normalized_location,
                flags=re.IGNORECASE,
            )
            for pattern in cls.TARGET_LOCATION_PATTERNS
        )

    # ==========================================================
    # SCORE
    # ==========================================================

    @staticmethod
    def _score(
        job: Job,
    ) -> float:
        """
        Return the best available deterministic selection score.

        overall_score is the primary score because it is produced
        by the deterministic intelligence layer.

        shortlist_likelihood_score is used only as a fallback.
        """

        if job.overall_score is not None:
            return float(job.overall_score)

        if job.shortlist_likelihood_score is not None:
            return float(job.shortlist_likelihood_score)

        return 0.0

    # ==========================================================
    # JOB METADATA
    # ==========================================================

    @staticmethod
    def _apply_decision(
        job: Job,
        decision: SelectionDecision,
    ) -> None:
        """
        Persist final-selection metadata on the canonical Job.
        """

        job.final_selection_eligible = decision.eligible

        job.final_selection_bucket = decision.bucket

        job.final_selection_reason = decision.reason

        job.final_selection_priority = decision.priority

    # ==========================================================
    # NORMALIZATION
    # ==========================================================

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        """
        Normalize text for deterministic matching.
        """

        if not value:
            return ""

        value = value.strip().lower()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value