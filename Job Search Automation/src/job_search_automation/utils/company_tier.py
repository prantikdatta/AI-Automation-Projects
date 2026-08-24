from __future__ import annotations

from typing import Dict


class CompanyTierClassifier:
    """
    Deterministic company classification.

    Returns

        Tier 1
        Tier 2
        Tier 3
        Unknown
    """

    TIERS: Dict[str, str] = {

        # --------------------------------------------------
        # FAANG / Big Tech
        # --------------------------------------------------

        "google": "Tier 1",
        "alphabet": "Tier 1",
        "amazon": "Tier 1",
        "microsoft": "Tier 1",
        "meta": "Tier 1",
        "apple": "Tier 1",
        "netflix": "Tier 1",
        "nvidia": "Tier 1",
        "openai": "Tier 1",

        # --------------------------------------------------
        # Consulting
        # --------------------------------------------------

        "mckinsey": "Tier 1",
        "bcg": "Tier 1",
        "bain": "Tier 1",
        "accenture": "Tier 1",
        "deloitte": "Tier 1",
        "ey": "Tier 1",
        "kpmg": "Tier 1",
        "pwc": "Tier 1",

        # --------------------------------------------------
        # Product
        # --------------------------------------------------

        "adobe": "Tier 1",
        "salesforce": "Tier 1",
        "atlassian": "Tier 1",
        "oracle": "Tier 1",
        "sap": "Tier 1",
        "servicenow": "Tier 1",
        "snowflake": "Tier 1",
        "databricks": "Tier 1",

        # --------------------------------------------------
        # Finance
        # --------------------------------------------------

        "jpmorgan": "Tier 1",
        "goldman sachs": "Tier 1",
        "morgan stanley": "Tier 1",
        "barclays": "Tier 1",
        "american express": "Tier 1",
        "visa": "Tier 1",
        "mastercard": "Tier 1",

        # --------------------------------------------------
        # Indian Product
        # --------------------------------------------------

        "flipkart": "Tier 1",
        "swiggy": "Tier 1",
        "zomato": "Tier 1",
        "razorpay": "Tier 1",
        "cred": "Tier 1",
        "groww": "Tier 1",
        "phonepe": "Tier 1",
        "paytm": "Tier 1",

        # --------------------------------------------------
        # Service Companies
        # --------------------------------------------------

        "tcs": "Tier 2",
        "infosys": "Tier 2",
        "wipro": "Tier 2",
        "hcl": "Tier 2",
        "capgemini": "Tier 2",
        "cognizant": "Tier 2",
        "ltimindtree": "Tier 2",
        "tech mahindra": "Tier 2",
        "persistent": "Tier 2",

    }

    @classmethod
    def classify(
        cls,
        company: str,
    ) -> str:

        if not company:
            return "Unknown"

        company = company.lower()

        for keyword, tier in cls.TIERS.items():

            if keyword in company:
                return tier

        return "Tier 3"