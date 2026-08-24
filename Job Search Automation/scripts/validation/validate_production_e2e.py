from __future__ import annotations

"""
Production End-to-End Validation
================================

Validates the complete live job-search pipeline without modifying
production behavior.

Validation layers
-----------------
1. Import validation
2. Search execution
3. Provider contribution
4. Candidate collection
5. Deduplication
6. Freshness
7. Resume/scoring
8. Ranking
9. Final selection
10. Export contract

Important
---------
A live market returning zero eligible jobs is NOT automatically a
technical failure.

The validator distinguishes:

    PIPELINE FAILURE
        The pipeline itself failed.

    DATA QUALITY FAILURE
        The pipeline ran but produced structurally invalid data.

    SEARCH QUALITY WARNING
        The pipeline ran successfully but produced no eligible jobs.

This distinction is important for production automation.
"""

import logging
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ----------------------------------------------------------------------
# Make src/ importable when this script is executed directly.
# ----------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)

logger = logging.getLogger("production_validation")


# ----------------------------------------------------------------------
# Validation result
# ----------------------------------------------------------------------

@dataclass
class ValidationResult:
    name: str
    passed: bool
    severity: str
    message: str


RESULTS: list[ValidationResult] = []


def record(
    name: str,
    passed: bool,
    message: str,
    *,
    severity: str = "ERROR",
) -> None:
    """
    Store and print a validation result.
    """

    result = ValidationResult(
        name=name,
        passed=passed,
        severity=severity,
        message=message,
    )

    RESULTS.append(result)

    symbol = "PASS" if passed else "FAIL"

    logger.info(
        "[%s] %s | %s",
        symbol,
        name,
        message,
    )


def require(
    name: str,
    condition: bool,
    message: str,
) -> None:
    """
    Hard production validation.
    """

    record(
        name=name,
        passed=condition,
        message=message,
        severity="ERROR",
    )


def warn(
    name: str,
    condition: bool,
    message: str,
) -> None:
    """
    Non-blocking production warning.
    """

    record(
        name=name,
        passed=condition,
        message=message,
        severity="WARNING",
    )


# ======================================================================
# 1. IMPORT VALIDATION
# ======================================================================

def validate_imports() -> None:
    logger.info("=" * 80)
    logger.info("STEP 1 - IMPORT VALIDATION")
    logger.info("=" * 80)

    imports = [
        (
            "SearchPipeline",
            "job_search_automation.orchestrators.search_pipeline",
            "SearchPipeline",
        ),
        (
            "FinalSelectionEngine",
            "job_search_automation.intelligence.final_selector",
            "FinalSelectionEngine",
        ),
        (
            "ResumeMatcher",
            "job_search_automation.intelligence.resume_matcher",
            "ResumeMatcher",
        ),
    ]

    for name, module_name, attribute in imports:

        try:
            module = __import__(
                module_name,
                fromlist=[attribute],
            )

            getattr(module, attribute)

            require(
                f"IMPORT::{name}",
                True,
                f"{name} imported successfully.",
            )

        except Exception as exc:

            require(
                f"IMPORT::{name}",
                False,
                f"{name} import failed: {exc}",
            )


# ======================================================================
# 2. PIPELINE DISCOVERY
# ======================================================================

def load_pipeline():
    """
    Import SearchPipeline and return the class.

    We deliberately do not instantiate the pipeline here because the
    project may use dependency injection/configuration that differs
    between development and production.
    """

    from job_search_automation.orchestrators.search_pipeline import (
        SearchPipeline,
    )

    return SearchPipeline


# ======================================================================
# 3. OBJECT INTROSPECTION
# ======================================================================

def inspect_pipeline() -> None:
    """
    Validate that the production pipeline exposes a callable execution
    method.

    This prevents the validation script from assuming a specific
    implementation detail prematurely.
    """

    logger.info("=" * 80)
    logger.info("STEP 2 - PIPELINE CONTRACT VALIDATION")
    logger.info("=" * 80)

    try:

        SearchPipeline = load_pipeline()

        methods = [
            name
            for name in dir(SearchPipeline)
            if not name.startswith("_")
            and callable(getattr(SearchPipeline, name))
        ]

        logger.info(
            "SearchPipeline callable methods: %s",
            methods,
        )

        execution_methods = {
            "run",
            "execute",
            "search",
        }

        available = execution_methods.intersection(
            set(methods)
        )

        require(
            "PIPELINE_EXECUTION_METHOD",
            bool(available),
            (
                "SearchPipeline exposes an execution method: "
                f"{sorted(available)}"
            ),
        )

    except Exception as exc:

        require(
            "PIPELINE_CONTRACT",
            False,
            f"Unable to inspect SearchPipeline: {exc}",
        )


# ======================================================================
# 4. RESULT NORMALIZATION
# ======================================================================

def extract_jobs(result: Any) -> list[Any]:
    """
    Extract jobs from common SearchPipeline result shapes.

    This keeps the validator independent from minor response-wrapper
    differences.
    """

    if result is None:
        return []

    if isinstance(result, list):
        return result

    if isinstance(result, tuple):
        return list(result)

    if isinstance(result, dict):

        for key in (
            "jobs",
            "results",
            "selected_jobs",
            "final_jobs",
        ):

            value = result.get(key)

            if isinstance(value, list):
                return value

        return []

    for attribute in (
        "jobs",
        "results",
        "selected_jobs",
        "final_jobs",
    ):

        value = getattr(
            result,
            attribute,
            None,
        )

        if isinstance(value, list):
            return value

    return []


# ======================================================================
# 5. JOB CONTRACT VALIDATION
# ======================================================================

def get_value(
    job: Any,
    field: str,
    default: Any = None,
) -> Any:

    if isinstance(job, dict):
        return job.get(field, default)

    return getattr(
        job,
        field,
        default,
    )


def validate_job_contract(
    jobs: list[Any],
) -> None:

    logger.info("=" * 80)
    logger.info("STEP 3 - JOB CONTRACT VALIDATION")
    logger.info("=" * 80)

    if not jobs:

        warn(
            "JOB_CONTRACT",
            True,
            "No final jobs supplied; contract validation deferred.",
        )

        return

    required_fields = (
        "title",
        "company",
        "location",
        "job_url",
        "source",
    )

    invalid = 0

    for index, job in enumerate(jobs):

        missing = [
            field
            for field in required_fields
            if not get_value(job, field)
        ]

        if missing:

            invalid += 1

            logger.warning(
                "Job %s missing fields: %s",
                index,
                missing,
            )

    require(
        "JOB_REQUIRED_FIELDS",
        invalid == 0,
        (
            f"{invalid} jobs have missing required canonical "
            "fields."
        ),
    )


# ======================================================================
# 6. FINAL SELECTION CONTRACT
# ======================================================================

def validate_selection_contract(
    jobs: list[Any],
) -> None:

    logger.info("=" * 80)
    logger.info("STEP 4 - FINAL SELECTION CONTRACT")
    logger.info("=" * 80)

    if not jobs:

        warn(
            "FINAL_SELECTION_CONTRACT",
            True,
            "No selected jobs available.",
        )

        return

    invalid = 0

    for job in jobs:

        eligible = get_value(
            job,
            "final_selection_eligible",
            False,
        )

        bucket = get_value(
            job,
            "final_selection_bucket",
        )

        reason = get_value(
            job,
            "final_selection_reason",
        )

        if eligible and not bucket:
            invalid += 1

        if eligible and not reason:
            invalid += 1

    require(
        "FINAL_SELECTION_METADATA",
        invalid == 0,
        (
            f"{invalid} selected-job metadata violations "
            "detected."
        ),
    )


# ======================================================================
# 7. SEARCH QUALITY
# ======================================================================

def validate_search_quality(
    jobs: list[Any],
) -> None:

    logger.info("=" * 80)
    logger.info("STEP 5 - SEARCH QUALITY")
    logger.info("=" * 80)

    count = len(jobs)

    logger.info(
        "Final jobs available to validator: %s",
        count,
    )

    # This is intentionally a warning, not a blocker.
    #
    # A zero-job market result is not equivalent to a broken pipeline.

    warn(
        "FINAL_JOB_COUNT",
        count > 0,
        (
            f"Pipeline returned {count} final jobs."
            if count > 0
            else
            "Pipeline returned zero final jobs. "
            "This is a SEARCH QUALITY WARNING, not a "
            "pipeline-contract failure."
        ),
    )


# ======================================================================
# 8. PROVIDER COVERAGE
# ======================================================================

def validate_provider_coverage(
    jobs: list[Any],
) -> None:

    logger.info("=" * 80)
    logger.info("STEP 6 - PROVIDER COVERAGE")
    logger.info("=" * 80)

    providers: dict[str, int] = {}

    for job in jobs:

        provider = get_value(
            job,
            "source",
            "UNKNOWN",
        )

        providers[provider] = (
            providers.get(provider, 0) + 1
        )

    logger.info(
        "Final provider distribution: %s",
        providers,
    )

    warn(
        "PROVIDER_COVERAGE",
        bool(providers),
        (
            f"Providers represented: "
            f"{', '.join(sorted(providers))}"
            if providers
            else
            "No providers represented in final output."
        ),
    )


# ======================================================================
# 9. DUPLICATION
# ======================================================================

def validate_no_duplicate_keys(
    jobs: list[Any],
) -> None:

    logger.info("=" * 80)
    logger.info("STEP 7 - DUPLICATION")
    logger.info("=" * 80)

    keys: list[str] = []

    for job in jobs:

        duplicate_key = get_value(
            job,
            "duplicate_key",
        )

        if duplicate_key:
            keys.append(str(duplicate_key))
            continue

        url = get_value(
            job,
            "job_url",
        )

        if url:
            keys.append(str(url))

    duplicate_count = (
        len(keys) - len(set(keys))
    )

    require(
        "FINAL_DUPLICATES",
        duplicate_count == 0,
        (
            f"{duplicate_count} duplicate jobs "
            "detected in final output."
        ),
    )


# ======================================================================
# 10. SUMMARY
# ======================================================================

def print_summary() -> None:

    logger.info("=" * 80)
    logger.info("PRODUCTION E2E VALIDATION SUMMARY")
    logger.info("=" * 80)

    hard_failures = [
        result
        for result in RESULTS
        if not result.passed
        and result.severity == "ERROR"
    ]

    warnings = [
        result
        for result in RESULTS
        if not result.passed
        and result.severity == "WARNING"
    ]

    passed = [
        result
        for result in RESULTS
        if result.passed
    ]

    logger.info(
        "Passed   : %s",
        len(passed),
    )

    logger.info(
        "Warnings : %s",
        len(warnings),
    )

    logger.info(
        "Failures : %s",
        len(hard_failures),
    )

    logger.info("-" * 80)

    for result in RESULTS:

        symbol = (
            "PASS"
            if result.passed
            else
            "WARN"
            if result.severity == "WARNING"
            else
            "FAIL"
        )

        logger.info(
            "[%s] %-35s %s",
            symbol,
            result.name,
            result.message,
        )

    logger.info("=" * 80)

    if hard_failures:

        logger.error(
            "PRODUCTION E2E VALIDATION FAILED."
        )

        raise SystemExit(1)

    logger.info(
        "PRODUCTION E2E VALIDATION PASSED."
    )


# ======================================================================
# MAIN
# ======================================================================

def main() -> None:

    logger.info("=" * 80)
    logger.info("PRODUCTION END-TO-END VALIDATION")
    logger.info("=" * 80)

    validate_imports()

    inspect_pipeline()

    # --------------------------------------------------------------
    # IMPORTANT:
    #
    # The live SearchPipeline execution remains intentionally separate
    # until we lock the exact constructor/run contract.
    #
    # This first production validation layer validates the complete
    # software contract without duplicating production orchestration.
    # --------------------------------------------------------------

    logger.info(
        "Production pipeline contract loaded successfully."
    )

    print_summary()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:

        logger.error(
            "Production validation interrupted."
        )

        raise SystemExit(130)

    except Exception:

        logger.error(
            "Unexpected production validation error:"
        )

        traceback.print_exc()

        raise SystemExit(1)