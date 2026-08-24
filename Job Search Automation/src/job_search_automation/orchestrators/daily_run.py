from __future__ import annotations

import logging
import sys
import time

from job_search_automation.orchestrators.search_pipeline import (
    SearchPipeline,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Production entry point for one scheduled job-search refresh.

    The scheduler is external (n8n). This function executes exactly one
    complete SearchPipeline run.

    Pipeline
    --------
    Providers
        ↓
    Deduplication
        ↓
    Freshness Filter
        ↓
    Enrichment
        ↓
    Resume Matching
        ↓
    Ranking
        ↓
    Final Selection
        ↓
    Google Sheets
    """

    start_time = time.perf_counter()

    logger.info("=" * 80)
    logger.info("Scheduled pipeline completed successfully.")
    logger.info("=" * 80)

    try:
        pipeline = SearchPipeline()

        response = pipeline.run()

        elapsed = round(
            time.perf_counter() - start_time,
            2,
        )

        logger.info("")
        logger.info("=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)

        logger.info(
            "Jobs Returned : %d",
            response.total_found,
        )

        logger.info(
            "Execution Time : %.2f seconds",
            elapsed,
        )

        if response.jobs:
            top = response.jobs[0]

            logger.info("")
            logger.info("Top Ranked Selected Job")
            logger.info("-" * 40)

            logger.info(
                "Title            : %s",
                top.title,
            )

            logger.info(
                "Company          : %s",
                top.company,
            )

            logger.info(
                "Location         : %s",
                top.location,
            )

            logger.info(
                "Overall Score    : %.2f",
                top.overall_score or 0.0,
            )

            # FinalSelectionEngine is authoritative for the
            # final application queue.
            logger.info(
                "Final Bucket     : %s",
                top.final_selection_bucket,
            )

            logger.info(
                "Eligible         : %s",
                top.final_selection_eligible,
            )

            logger.info(
                "Decision Reason  : %s",
                top.final_selection_reason,
            )

            logger.info(
                "Final Priority   : %s",
                top.final_selection_priority,
            )

        else:
            logger.warning(
                "No jobs were returned."
            )

        logger.info("=" * 80)
        logger.info(
            "Daily pipeline completed successfully."
        )
        logger.info("=" * 80)

        return 0

    except Exception:
        logger.exception(
            "Daily pipeline execution failed."
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())