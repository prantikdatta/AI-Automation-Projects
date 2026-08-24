from __future__ import annotations

import logging

from job_search_automation.clients.smartrecruiters_client import (
    SmartRecruitersClient,
)
from job_search_automation.models.job import Job
from job_search_automation.normalizers.canonical_mapper import (
    CanonicalMapper,
)
from job_search_automation.normalizers.smartrecruiters import (
    SmartRecruitersNormalizer,
)
from job_search_automation.providers.ats_provider import (
    ATSProvider,
)
from job_search_automation.providers.capabilities import (
    ProviderCapabilities,
)
from job_search_automation.providers.metadata import (
    ProviderMetadata,
)

logger = logging.getLogger("job_search_automation")


class SmartRecruitersProvider(ATSProvider):

    COMPANY_BOARDS = [
        "visa",
        "adobe",
        "ikea",
        "bosch",
        "wolt",
        "uber",
        "myntra",
        "flipkart",
        "publicissapient",
        "olx",
    ]

    def __init__(self) -> None:
        self.client = SmartRecruitersClient()
        self.normalizer = SmartRecruitersNormalizer()

    @property
    def name(self) -> str:
        return "SmartRecruiters"

    @property
    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name="smartrecruiters",
            version="1.0",
            provider_type="ATS",
            capabilities=ProviderCapabilities(
                supports_location=False,
                supports_remote=False,
                supports_salary=False,
                supports_company_filter=True,
                supports_posted_date=True,
                supports_multiple_roles=True,
                requires_local_filtering=True,
            ),
        )

    def fetch_jobs(self) -> list[Job]:

        jobs: list[Job] = []

        logger.info(
            "Starting SmartRecruiters provider (%d companies)",
            len(self.COMPANY_BOARDS),
        )

        for company in self.COMPANY_BOARDS:

            logger.info(
                "SMARTRECRUITERS REQUEST -> %s",
                company,
            )

            try:
                payload = self.client.search_jobs(company)

            except Exception:
                logger.exception(
                    "SmartRecruiters request failed for company '%s'",
                    company,
                )
                continue

            postings = payload.get("content", [])

            logger.info(
                "%s returned %d postings.",
                company,
                len(postings),
            )

            for raw_job in postings:

                try:
                    normalized = self.normalizer.normalize(
                        raw=raw_job,
                        searched_role="",
                    )

                    job = CanonicalMapper.to_job(normalized)

                    jobs.append(job)

                except Exception:
                    logger.exception(
                        "Failed to normalize SmartRecruiters job from company '%s'",
                        company,
                    )

        logger.info(
            "SmartRecruiters returned %d jobs.",
            len(jobs),
        )

        return jobs