from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class ApifyNormalizer(BaseNormalizer):

    provider_name = "Apify"

    _GOOGLE_HOSTS = {
        "google.com",
        "www.google.com",
        "google.co.in",
        "www.google.co.in",
        "google.co.uk",
        "www.google.co.uk",
    }

    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:
        """
        Normalize Thirdwatch LinkedIn Jobs Apify dataset items.

        The canonical model remains provider-independent.

        URL priority:

        1. Explicit application/job URL fields
        2. applyOptions destination URL
        3. Nested job/application URL fields
        4. Generic URL fields only when they are not Google result URLs
        """

        # ==========================================================
        # POSTED DATE
        # ==========================================================

        posted_at = None

        posted = (
            raw.get("postedAtIso")
            or raw.get("postedAt")
            or raw.get("posted_at")
            or raw.get("datePosted")
        )

        if posted:
            try:
                posted_at = datetime.fromisoformat(
                    str(posted).replace(
                        "Z",
                        "+00:00",
                    )
                )
            except (TypeError, ValueError):
                posted_at = None

        # ==========================================================
        # SALARY
        # ==========================================================

        salary_min = (
            raw.get("salaryMin")
            or raw.get("salary_min")
        )

        salary_max = (
            raw.get("salaryMax")
            or raw.get("salary_max")
        )

        currency = (
            raw.get("salaryCurrency")
            or raw.get("currency")
            or raw.get("salary_currency")
        )

        # ==========================================================
        # REMOTE / WORK MODE
        # ==========================================================

        remote = bool(
            raw.get("workFromHome")
            or raw.get("remote")
            or raw.get("isRemote")
        )

        work_mode = (
            "Remote"
            if remote
            else "Onsite"
        )

        # ==========================================================
        # JOB URL
        # ==========================================================

        job_url = self._extract_job_url(raw)

        # ==========================================================
        # COMPANY
        # ==========================================================

        company = (
            raw.get("companyName")
            or raw.get("company")
            or raw.get("company_name")
            or ""
        )

        # ==========================================================
        # EMPLOYMENT TYPE
        # ==========================================================

        employment_type = (
            raw.get("jobType")
            or raw.get("employmentType")
            or raw.get("employment_type")
        )

        # ==========================================================
        # NORMALIZED JOB
        # ==========================================================

        return NormalizedJob(
            searched_role=searched_role,
            title=raw.get(
                "title",
                "",
            ),
            company=company,
            location=raw.get(
                "location",
                "",
            ),
            description=raw.get(
                "description",
                "",
            ),
            job_url=job_url,
            provider=self.provider_name,
            source=self.provider_name,
            posted_at=posted_at,
            employment_type=employment_type,
            seniority=raw.get(
                "seniority",
            ),
            remote=remote,
            work_mode=work_mode,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            salary_confidence=(
                1.0
                if salary_min or salary_max
                else None
            ),
            skills=[],
            raw=raw,
        )

    # ==============================================================
    # URL EXTRACTION
    # ==============================================================

    @classmethod
    def _is_google_result_url(
        cls,
        value: Any,
    ) -> bool:
        """
        Return True when a URL points back to Google rather than
        the actual employer/application destination.
        """

        if not isinstance(value, str):
            return False

        value = value.strip()

        if not value:
            return False

        try:
            parsed = urlparse(value)
        except ValueError:
            return False

        hostname = (
            parsed.hostname
            or ""
        ).lower()

        if hostname in cls._GOOGLE_HOSTS:
            return True

        return hostname.endswith(".google.com")

    @classmethod
    def _valid_url(
        cls,
        value: Any,
        *,
        allow_google: bool = False,
    ) -> str:
        """
        Return a cleaned URL only when it is a non-empty string.

        Google result URLs are rejected by default because they are not
        canonical employer/application URLs.
        """

        if not isinstance(value, str):
            return ""

        value = value.strip()

        if not value:
            return ""

        if not allow_google and cls._is_google_result_url(value):
            return ""

        return value

    @classmethod
    def _extract_job_url(
        cls,
        raw: dict[str, Any],
    ) -> str:
        """
        Extract the canonical destination URL from an Apify item.

        Important:
        `link` / generic `url` fields can represent the provider/search result
        rather than the actual employer destination. Therefore
        applyOptions is checked before those generic fields.
        """

        # ----------------------------------------------------------
        # 1. Explicit application/job URL fields
        # ----------------------------------------------------------

        explicit_fields = (
            "jobUrl",
            "job_url",
            "applyUrl",
            "apply_url",
            "applicationUrl",
            "application_url",
        )

        for field in explicit_fields:
            candidate = cls._valid_url(
                raw.get(field)
            )

            if candidate:
                return candidate

        # ----------------------------------------------------------
        # 2. applyOptions
        # ----------------------------------------------------------

        apply_options = raw.get(
            "applyOptions",
            [],
        )

        if isinstance(apply_options, list):
            for option in apply_options:
                if not isinstance(option, dict):
                    continue

                option_fields = (
                    "link",
                    "url",
                    "applyUrl",
                    "apply_url",
                    "applicationUrl",
                    "application_url",
                )

                for field in option_fields:
                    candidate = cls._valid_url(
                        option.get(field)
                    )

                    if candidate:
                        return candidate

        # ----------------------------------------------------------
        # 3. Nested job/application objects
        # ----------------------------------------------------------

        nested_objects = (
            raw.get("job"),
            raw.get("application"),
            raw.get("jobDetails"),
            raw.get("job_details"),
        )

        for nested in nested_objects:
            if not isinstance(nested, dict):
                continue

            for field in explicit_fields:
                candidate = cls._valid_url(
                    nested.get(field)
                )

                if candidate:
                    return candidate

            nested_apply_options = nested.get(
                "applyOptions",
                [],
            )

            if isinstance(
                nested_apply_options,
                list,
            ):
                for option in nested_apply_options:
                    if not isinstance(option, dict):
                        continue

                    for field in (
                        "link",
                        "url",
                        "applyUrl",
                        "apply_url",
                        "applicationUrl",
                        "application_url",
                    ):
                        candidate = cls._valid_url(
                            option.get(field)
                        )

                        if candidate:
                            return candidate

        # ----------------------------------------------------------
        # 4. Generic URL fields
        # ----------------------------------------------------------

        for field in (
            "url",
            "link",
        ):
            candidate = cls._valid_url(
                raw.get(field)
            )

            if candidate:
                return candidate

        return ""