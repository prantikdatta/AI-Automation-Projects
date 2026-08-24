from __future__ import annotations

from job_search_automation.ats.board import ATSBoard
from job_search_automation.config.company_registry import COMPANY_REGISTRY


class ATSRegistry:
    @staticmethod
    def boards(
        ats: str,
        verified_only: bool = True,
    ) -> list[ATSBoard]:
        boards: list[ATSBoard] = []

        for company in COMPANY_REGISTRY:
            if company["ats"] != ats:
                continue

            verified = bool(company.get("verified", False))

            if verified_only and not verified:
                continue

            boards.append(
                ATSBoard(
                    company=company["company"],
                    ats=company["ats"],
                    board=company["board"],
                    verified=verified,
                )
            )

        return boards