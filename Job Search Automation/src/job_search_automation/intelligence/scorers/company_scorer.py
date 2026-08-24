from __future__ import annotations

from job_search_automation.config.company_preferences import (
    BANKS,
    COMPANY_ALIASES,
    COMPANY_TIER_SCORE,
    CONSULTING_COMPANIES,
    FINTECH_COMPANIES,
    GCC_COMPANIES,
    PRODUCT_COMPANIES,
    TIER_1_COMPANIES,
    UNICORNS,
)
from job_search_automation.intelligence.models import (
    CompanyScoreResult,
)


class CompanyScorer:
    """
    Scores a company based on configurable company tiers.
    """

    def __init__(self) -> None:

        self.aliases = {
            key.lower(): value
            for key, value in COMPANY_ALIASES.items()
        }

    def score(
        self,
        company_name: str,
    ) -> CompanyScoreResult:

        company_name = (company_name or "").strip()

        canonical_name = self.aliases.get(
            company_name.lower(),
            company_name,
        )

        company_tier = "Other"

        explanation = (
            "Company is not classified into a preferred tier."
        )

        if canonical_name in TIER_1_COMPANIES:

            company_tier = "Tier1"

            explanation = (
                "Tier-1 global employer."
            )

        elif canonical_name in CONSULTING_COMPANIES:

            company_tier = "Consulting"

            explanation = (
                "Premium consulting organization."
            )

        elif canonical_name in PRODUCT_COMPANIES:

            company_tier = "Product"

            explanation = (
                "Established product company."
            )

        elif canonical_name in FINTECH_COMPANIES:

            company_tier = "FinTech"

            explanation = (
                "High-priority FinTech company."
            )

        elif canonical_name in BANKS:

            company_tier = "Bank"

            explanation = (
                "Leading banking or financial institution."
            )

        elif canonical_name in GCC_COMPANIES:

            company_tier = "GCC"

            explanation = (
                "Global Capability Centre."
            )

        elif canonical_name in UNICORNS:

            company_tier = "Unicorn"

            explanation = (
                "Recognized unicorn startup."
            )

        score = COMPANY_TIER_SCORE.get(
            company_tier,
            COMPANY_TIER_SCORE["Other"],
        )

        return CompanyScoreResult(

            score=score,

            company_name=company_name,

            normalized_company_name=canonical_name,

            company_tier=company_tier,

            industry=None,

            explanation=explanation,

            confidence=1.0,

            metadata={

                "original_company": company_name,

                "normalized_company": canonical_name,

                "tier": company_tier,

            },

        )