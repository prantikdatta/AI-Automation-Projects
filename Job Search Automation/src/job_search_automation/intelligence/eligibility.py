from __future__ import annotations

import re

from job_search_automation.models.job import Job


class JobEligibilityEngine:
    """
    Deterministic hard-eligibility engine.

    This layer answers:

        "Is this job actually relevant enough to enter
         the final selection process?"

    It does NOT score jobs.

    It does NOT call Gemini.

    It does NOT rank jobs.

    It does NOT perform final application prioritization.

    It only applies hard business constraints:

        Role relevance
        Location eligibility
        Remote eligibility
    """

    # ==========================================================
    # TARGET ROLE FAMILIES
    # ==========================================================

    ROLE_PATTERNS: tuple[str, ...] = (
        r"\bdata analyst\b",
        r"\bsenior data analyst\b",
        r"\banalytics analyst\b",
        r"\banalytics engineer\b",
        r"\banalytics engineering\b",
        r"\breporting analyst\b",
        r"\bbusiness intelligence analyst\b",
        r"\bbi analyst\b",
        r"\bbusiness intelligence developer\b",
        r"\bbi developer\b",
        r"\binsights analyst\b",
        r"\bdecision scientist\b",
        r"\banalytics consultant\b",
        r"\bdata consultant\b",
        r"\bproduct analyst\b",
        r"\bproduct analytics\b",
        r"\bstrategy analyst\b",
        r"\bstrategy and analytics\b",
        r"\bstrategy & analytics\b",
        r"\bbusiness analyst\b",
        r"\btechnical program manager\b",
        r"\bprogram manager\b",
        r"\bprogram management\b",
        r"\btechnical program management\b",
        r"\bproject management office\b",
        r"\bpmo\b",
        r"\btransformation\b",
        r"\boperations analyst\b",
        r"\boperations analytics\b",
        r"\brisk analyst\b",
        r"\bcredit risk analyst\b",
        r"\bfintech analyst\b",
        r"\bfinancial analyst\b",
        r"\bproduct operations\b",
    )

    # Explicitly incompatible role families.
    REJECT_PATTERNS: tuple[str, ...] = (
        r"\bcopywriter\b",
        r"\bcontent writer\b",
        r"\bcontent strategist\b",
        r"\bgraphic designer\b",
        r"\bui designer\b",
        r"\bux designer\b",
        r"\bsales representative\b",
        r"\bsales executive\b",
        r"\baccount executive\b",
        r"\bcustomer support\b",
        r"\bcustomer service\b",
        r"\bservice desk\b",
        r"\bhelp desk\b",
        r"\bnetwork engineer\b",
        r"\bsystems administrator\b",
        r"\bsystem administrator\b",
        r"\bdesktop support\b",
        r"\btechnical support\b",
        r"\bsoftware engineer\b",
        r"\bfrontend engineer\b",
        r"\bbackend engineer\b",
        r"\bfull stack engineer\b",
        r"\bdevops engineer\b",
        r"\bqa engineer\b",
        r"\btest engineer\b",
        r"\bmechanical engineer\b",
        r"\bcivil engineer\b",
        r"\belectrical engineer\b",
        r"\bdata entry\b",
        r"\brecruiter\b",
        r"\bhuman resources\b",
        r"\bhr manager\b",
    )

    # ==========================================================
    # TARGET LOCATIONS
    # ==========================================================

    TARGET_LOCATIONS: tuple[str, ...] = (
        "mumbai",
        "navi mumbai",
        "thane",
        "bangalore",
        "bengaluru",
        "hyderabad",
    )

    REMOTE_TERMS: tuple[str, ...] = (
        "remote",
        "work from home",
        "wfh",
        "fully remote",
        "100% remote",
        "remote anywhere",
    )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def evaluate(
        self,
        job: Job,
    ) -> tuple[bool, str]:
        """
        Evaluate hard eligibility rules.

        Returns
        -------
        tuple[bool, str]
            (eligible, reason)
        """

        role_ok, role_reason = self.check_role(job)

        if not role_ok:
            return False, role_reason

        location_ok, location_reason = self.check_location(job)

        if not location_ok:
            return False, location_reason

        return (
            True,
            "Passed role and location eligibility.",
        )

    # ==========================================================
    # ROLE ELIGIBILITY
    # ==========================================================

    def check_role(
        self,
        job: Job,
    ) -> tuple[bool, str]:
        """
        Determine whether the job belongs to a target role family.
        """

        title = self._normalise(
            job.title,
        )

        if not title:
            return (
                False,
                "Rejected: missing job title.",
            )

        # ------------------------------------------------------
        # Explicit incompatible role gate.
        # ------------------------------------------------------

        rejected_match = self._find_match(
            title,
            self.REJECT_PATTERNS,
        )

        if rejected_match:
            return (
                False,
                f"Rejected: incompatible role family "
                f"('{rejected_match}').",
            )

        # ------------------------------------------------------
        # Positive role gate.
        # ------------------------------------------------------

        target_match = self._find_match(
            title,
            self.ROLE_PATTERNS,
        )

        if target_match:
            return (
                True,
                f"Role matched target family "
                f"('{target_match}').",
            )

        # ------------------------------------------------------
        # Job bucket can provide secondary evidence.
        # ------------------------------------------------------

        job_bucket = self._normalise(
            job.job_bucket,
        )

        if job_bucket:
            bucket_match = self._find_match(
                job_bucket,
                self.ROLE_PATTERNS,
            )

            if bucket_match:
                return (
                    True,
                    f"Role accepted through job bucket "
                    f"('{bucket_match}').",
                )

        return (
            False,
            "Rejected: title does not match a target role family.",
        )

    # ==========================================================
    # LOCATION ELIGIBILITY
    # ==========================================================

    def check_location(
        self,
        job: Job,
    ) -> tuple[bool, str]:
        """
        Determine whether the job is geographically eligible.
        """

        location = self._normalise(
            job.location,
        )

        work_mode = self._normalise(
            job.work_mode,
        )

        # ------------------------------------------------------
        # Explicit remote classification.
        # ------------------------------------------------------

        if (
            job.remote
            or self._contains_any(
                location,
                self.REMOTE_TERMS,
            )
            or self._contains_any(
                work_mode,
                self.REMOTE_TERMS,
            )
        ):
            return (
                True,
                "Location accepted: remote role.",
            )

        # ------------------------------------------------------
        # Target Indian locations.
        # ------------------------------------------------------

        for target in self.TARGET_LOCATIONS:
            if self._contains_location(
                location,
                target,
            ):
                return (
                    True,
                    f"Location accepted: {target}.",
                )

        return (
            False,
            f"Rejected: location '{job.location}' "
            f"is outside the target geography.",
        )

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _normalise(
        value: str | None,
    ) -> str:
        """
        Normalize text for deterministic matching.
        """

        if not value:
            return ""

        value = str(value).strip().lower()

        value = value.replace(
            "&",
            " and ",
        )

        value = re.sub(
            r"[^a-z0-9%]+",
            " ",
            value,
        )

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @staticmethod
    def _find_match(
        text: str,
        patterns: tuple[str, ...],
    ) -> str | None:
        """
        Return the first matching pattern in readable form.
        """

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    @staticmethod
    def _contains_any(
        text: str,
        values: tuple[str, ...],
    ) -> bool:
        """
        Determine whether normalized text contains any target term.
        """

        if not text:
            return False

        return any(
            value in text
            for value in values
        )

    @staticmethod
    def _contains_location(
        location: str,
        target: str,
    ) -> bool:
        """
        Match a location while avoiding overly broad substring matches.
        """

        normalized_target = (
            target.strip().lower()
        )

        if not normalized_target:
            return False

        pattern = (
            rf"\b{re.escape(normalized_target)}\b"
        )

        return bool(
            re.search(
                pattern,
                location,
                flags=re.IGNORECASE,
            )
        )