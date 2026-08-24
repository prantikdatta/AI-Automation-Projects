from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any


# ============================================================================
# PROJECT BOOTSTRAP
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("provider-health-validation")


# ============================================================================
# RESULT
# ============================================================================


class ProviderHealthResult:
    def __init__(self) -> None:
        self.passed = 0
        self.warnings = 0
        self.failures = 0

    def passed_(self, name: str, message: str) -> None:
        self.passed += 1
        logger.info("[PASS] %-35s | %s", name, message)

    def warning(self, name: str, message: str) -> None:
        self.warnings += 1
        logger.warning("[WARN] %-35s | %s", name, message)

    def failed(self, name: str, message: str) -> None:
        self.failures += 1
        logger.error("[FAIL] %-35s | %s", name, message)


# ============================================================================
# PROVIDER DISCOVERY
# ============================================================================


def discover_providers(result: ProviderHealthResult) -> list[Any]:
    logger.info("=" * 80)
    logger.info("PROVIDER HEALTH VALIDATION")
    logger.info("=" * 80)

    providers: list[Any] = []

    try:
        from job_search_automation.providers.adzuna import AdzunaProvider

        providers.append(AdzunaProvider)
        result.passed_(
            "PROVIDER::Adzuna",
            "Adzuna provider import succeeded.",
        )
    except Exception as exc:
        result.warning(
            "PROVIDER::Adzuna",
            f"Adzuna unavailable: {exc}",
        )

    try:
        from job_search_automation.providers.rapidapi import RapidAPIProvider

        providers.append(RapidAPIProvider)
        result.passed_(
            "PROVIDER::RapidAPI",
            "RapidAPI provider import succeeded.",
        )
    except Exception as exc:
        result.warning(
            "PROVIDER::RapidAPI",
            f"RapidAPI unavailable: {exc}",
        )

    try:
        from job_search_automation.providers.remotive import RemotiveProvider

        providers.append(RemotiveProvider)
        result.passed_(
            "PROVIDER::Remotive",
            "Remotive provider import succeeded.",
        )
    except Exception as exc:
        result.warning(
            "PROVIDER::Remotive",
            f"Remotive unavailable: {exc}",
        )

    return providers


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    result = ProviderHealthResult()

    providers = discover_providers(result)

    if not providers:
        result.failed(
            "PROVIDERS::DISCOVERY",
            "No API providers could be imported.",
        )

    logger.info("=" * 80)
    logger.info("PROVIDER HEALTH SUMMARY")
    logger.info("=" * 80)

    logger.info("Providers discovered : %s", len(providers))
    logger.info("Passed               : %s", result.passed)
    logger.info("Warnings             : %s", result.warnings)
    logger.info("Failures             : %s", result.failures)

    if result.failures:
        logger.error("PROVIDER HEALTH VALIDATION FAILED.")
        return 1

    logger.info("PROVIDER HEALTH VALIDATION PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())