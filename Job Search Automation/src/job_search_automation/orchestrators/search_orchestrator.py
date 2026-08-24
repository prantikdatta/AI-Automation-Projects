from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Iterable

from job_search_automation.intelligence.search_strategy_engine import (
    SearchStrategyEngine,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.providers.provider_manager import ProviderManager
from job_search_automation.providers.provider_router import ProviderRouter
from job_search_automation.services import logger
from job_search_automation.utils.job_prefilter import should_reject


# ============================================================================
# COLLECTION POLICY
# ============================================================================

# These are candidate-universe targets.
#
# They are NOT:
#   - final application limits
#   - ranking limits
#   - freshness limits
#
# The downstream SearchPipeline decides what is ultimately selected.

TARGET_API_POOL = 100
TARGET_ATS_POOL = 60

# Provider-level request size.
DEFAULT_SEARCH_LIMIT = 30

# IMPORTANT:
# Do NOT constrain collection by posting age.
#
# Freshness is handled later by the production pipeline.
DEFAULT_POSTED_WITHIN_DAYS = None


# Providers backed by ATS platforms.
ATS_PROVIDERS = {
    "greenhouse",
    "ashby",
    "lever",
    "smartrecruiters",
}


class SearchOrchestrator:
    """
    Production job-search collection orchestrator.

    Responsibilities
    ----------------
    1. Build the complete search strategy.
    2. Convert strategy plans into SearchRequest objects.
    3. Route requests through ProviderRouter.
    4. Execute providers through ProviderManager.
    5. Apply only the cheap prefilter.
    6. Maintain API and ATS candidate pools.
    7. Preserve breadth across role/location/priority plans.
    8. Continue searching until collection targets are reached
       or all strategy plans have been exhausted.

    The orchestrator does NOT:
        - globally deduplicate jobs
        - apply freshness scoring
        - perform enrichment
        - perform resume matching
        - call Gemini
        - rank jobs
        - perform final selection
        - export jobs
    """

    def __init__(
        self,
        *,
        target_api_pool: int = TARGET_API_POOL,
        target_ats_pool: int = TARGET_ATS_POOL,
    ) -> None:
        self.target_api_pool = max(
            0,
            target_api_pool,
        )

        self.target_ats_pool = max(
            0,
            target_ats_pool,
        )

        # SearchStrategyEngine remains the authority for:
        #
        #   roles
        #   locations
        #   buckets
        #   priorities
        #
        self.search_plans = SearchStrategyEngine.build()

    # ========================================================================
    # PUBLIC ENTRYPOINT
    # ========================================================================

    def collect_jobs(self) -> list[Job]:
        """
        Execute the complete search strategy.

        Returns the broad candidate universe.

        No freshness restriction is applied here.
        """

        api_jobs: list[Job] = []
        ats_jobs: list[Job] = []

        provider_totals: DefaultDict[str, int] = defaultdict(int)

        logger.info("")
        logger.info("=" * 90)
        logger.info("SEARCH ORCHESTRATOR")
        logger.info("=" * 90)

        logger.info(
            "Search plans      : %d",
            len(self.search_plans),
        )

        logger.info(
            "API target pool   : %d",
            self.target_api_pool,
        )

        logger.info(
            "ATS target pool   : %d",
            self.target_ats_pool,
        )

        logger.info(
            "Search freshness  : UNRESTRICTED",
        )

        # --------------------------------------------------------------------
        # Execute every strategy plan until collection targets are reached.
        # --------------------------------------------------------------------

        for index, plan in enumerate(
            self.search_plans,
            start=1,
        ):
            if self._targets_reached(
                api_jobs,
                ats_jobs,
            ):
                logger.info(
                    "Collection targets already reached."
                )
                break

            try:
                request = self._build_request(
                    plan,
                )

            except Exception:
                logger.exception(
                    "Invalid search plan %d. Skipping.",
                    index,
                )
                continue

            logger.info("")
            logger.info(
                "-" * 90,
            )

            logger.info(
                "SEARCH PLAN %d/%d",
                index,
                len(self.search_plans),
            )

            logger.info(
                "Roles     : %s",
                ", ".join(request.roles),
            )

            logger.info(
                "Locations : %s",
                ", ".join(request.locations),
            )

            logger.info(
                "Bucket    : %s",
                request.bucket,
            )

            logger.info(
                "Priority  : %s",
                request.priority,
            )

            logger.info(
                "Limit     : %d",
                request.limit,
            )

            logger.info(
                "Freshness : UNRESTRICTED",
            )

            # ----------------------------------------------------------------
            # Provider routing
            # ----------------------------------------------------------------

            try:
                providers = ProviderRouter.route(
                    request,
                )

            except Exception:
                logger.exception(
                    "Provider routing failed for plan %d.",
                    index,
                )
                continue

            if not providers:
                logger.warning(
                    "No providers available for plan %d.",
                    index,
                )
                continue

            provider_names = [
                self._provider_name(provider)
                for provider in providers
            ]

            logger.info(
                "Providers : %s",
                ", ".join(provider_names),
            )

            # ----------------------------------------------------------------
            # Provider execution
            # ----------------------------------------------------------------

            manager = ProviderManager(
                providers,
            )

            try:
                provider_results = (
                    manager.search_by_provider(
                        request,
                    )
                )

            except Exception:
                logger.exception(
                    "Provider execution failed for plan %d.",
                    index,
                )
                continue

            # ----------------------------------------------------------------
            # Candidate collection
            # ----------------------------------------------------------------

            self._collect_provider_results(
                provider_results=provider_results,
                api_jobs=api_jobs,
                ats_jobs=ats_jobs,
                provider_totals=provider_totals,
            )

            logger.info("")
            logger.info(
                "POOL STATUS | API=%d/%d | ATS=%d/%d | TOTAL=%d",
                len(api_jobs),
                self.target_api_pool,
                len(ats_jobs),
                self.target_ats_pool,
                len(api_jobs) + len(ats_jobs),
            )

        # --------------------------------------------------------------------
        # Final collection report
        # --------------------------------------------------------------------

        self._log_provider_report(
            provider_totals,
        )

        logger.info("")
        logger.info("=" * 90)
        logger.info("SEARCH COLLECTION COMPLETED")
        logger.info("=" * 90)

        logger.info(
            "API candidates : %d",
            len(api_jobs),
        )

        logger.info(
            "ATS candidates : %d",
            len(ats_jobs),
        )

        logger.info(
            "Total          : %d",
            len(api_jobs) + len(ats_jobs),
        )

        logger.info(
            "API target met : %s",
            len(api_jobs) >= self.target_api_pool,
        )

        logger.info(
            "ATS target met : %s",
            len(ats_jobs) >= self.target_ats_pool,
        )

        logger.info("=" * 90)

        return api_jobs + ats_jobs

    # ========================================================================
    # REQUEST BUILDING
    # ========================================================================

    @staticmethod
    def _build_request(
        plan: dict,
    ) -> SearchRequest:
        """
        Convert one strategy plan into a SearchRequest.

        SearchStrategyEngine owns search intent.

        SearchOrchestrator owns operational collection settings.
        """

        roles = SearchOrchestrator._normalise_roles(
            plan.get("roles"),
        )

        location = str(
            plan.get("location") or "",
        ).strip()

        if not roles:
            raise ValueError(
                "Search strategy plan contains no roles.",
            )

        if not location:
            raise ValueError(
                "Search strategy plan contains no location.",
            )

        return SearchRequest(
            searched_role=" OR ".join(roles),
            roles=roles,
            bucket=plan.get("bucket"),
            priority=plan.get("priority"),
            keywords=roles,
            locations=[
                location,
            ],
            limit=int(
                plan.get(
                    "target_jobs",
                    DEFAULT_SEARCH_LIMIT,
                )
            ),
            remote_only=False,

            # --------------------------------------------------------------
            # IMPORTANT
            #
            # Do not restrict the provider search by age.
            #
            # A job can still be active after 14/30 days.
            # Freshness is evaluated downstream.
            # --------------------------------------------------------------
            posted_within_days=DEFAULT_POSTED_WITHIN_DAYS,
        )

    @staticmethod
    def _normalise_roles(
        roles: Iterable[str] | None,
    ) -> list[str]:
        """
        Normalize role names while preserving strategy order.
        """

        if not roles:
            return []

        normalized: list[str] = []
        seen: set[str] = set()

        for role in roles:
            value = str(
                role,
            ).strip()

            if not value:
                continue

            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(value)

        return normalized

    # ========================================================================
    # RESULT COLLECTION
    # ========================================================================

    def _collect_provider_results(
        self,
        *,
        provider_results: dict[str, list[Job]],
        api_jobs: list[Job],
        ats_jobs: list[Job],
        provider_totals: DefaultDict[str, int],
    ) -> None:
        """
        Process one ProviderManager result set.

        Only cheap rejection occurs here.

        Global deduplication remains downstream.
        """

        for provider_name, jobs in provider_results.items():
            provider_key = self._provider_name(
                provider_name,
            )

            raw_count = len(jobs)

            accepted = self._prefilter_jobs(
                jobs,
            )

            accepted_count = len(
                accepted,
            )

            provider_totals[
                provider_key
            ] += accepted_count

            is_ats = self._is_ats_provider(
                provider_key,
            )

            if is_ats:
                ats_jobs.extend(
                    accepted,
                )
            else:
                api_jobs.extend(
                    accepted,
                )

            logger.info(
                "%-20s | raw=%4d | accepted=%4d | pool=%s",
                provider_key,
                raw_count,
                accepted_count,
                "ATS" if is_ats else "API",
            )

    # ========================================================================
    # LIGHTWEIGHT PREFILTER
    # ========================================================================

    @staticmethod
    def _prefilter_jobs(
        jobs: Iterable[Job],
    ) -> list[Job]:
        """
        Apply only the inexpensive rejection rules.

        This is NOT final job qualification.

        The expensive business logic remains downstream.
        """

        accepted: list[Job] = []

        for job in jobs:
            try:
                if should_reject(
                    job,
                ):
                    continue

                accepted.append(
                    job,
                )

            except Exception:
                logger.exception(
                    "Prefilter failed for '%s' at '%s'. "
                    "Rejecting job safely.",
                    getattr(
                        job,
                        "title",
                        "",
                    ),
                    getattr(
                        job,
                        "company",
                        "",
                    ),
                )

        return accepted

    # ========================================================================
    # PROVIDER CLASSIFICATION
    # ========================================================================

    @staticmethod
    def _provider_name(
        provider: object,
    ) -> str:
        """
        Normalize provider identifiers.

        Supports:
            - strings
            - provider objects
            - provider_name attributes
        """

        if isinstance(
            provider,
            str,
        ):
            return provider.strip().lower()

        for attribute in (
            "name",
            "provider_name",
        ):
            value = getattr(
                provider,
                attribute,
                None,
            )

            if value:
                return str(
                    value,
                ).strip().lower()

        return str(
            provider,
        ).strip().lower()

    @staticmethod
    def _is_ats_provider(
        provider_name: str,
    ) -> bool:
        """
        Determine whether a provider belongs to the ATS pool.
        """

        return (
            provider_name.strip().lower()
            in ATS_PROVIDERS
        )

    # ========================================================================
    # COLLECTION POLICY
    # ========================================================================

    def _targets_reached(
        self,
        api_jobs: list[Job],
        ats_jobs: list[Job],
    ) -> bool:
        """
        Determine whether both candidate pools are sufficiently populated.
        """

        return (
            len(api_jobs) >= self.target_api_pool
            and
            len(ats_jobs) >= self.target_ats_pool
        )

    # ========================================================================
    # REPORTING
    # ========================================================================

    @staticmethod
    def _log_provider_report(
        provider_totals: dict[str, int],
    ) -> None:
        """
        Emit provider contribution statistics.
        """

        logger.info("")
        logger.info("=" * 90)
        logger.info(
            "PROVIDER CONTRIBUTION REPORT",
        )
        logger.info("=" * 90)

        total = 0

        for provider_name in sorted(
            provider_totals,
        ):
            count = provider_totals[
                provider_name
            ]

            total += count

            logger.info(
                "%-25s %6d jobs",
                provider_name,
                count,
            )

        logger.info(
            "-" * 90,
        )

        logger.info(
            "%-25s %6d jobs",
            "TOTAL",
            total,
        )

        logger.info("=" * 90)