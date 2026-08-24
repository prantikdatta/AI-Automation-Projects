from __future__ import annotations

from typing import List

from job_search_automation.application.workflow import (
    ApplicationWorkflow,
)
from job_search_automation.enrichment.pipeline import (
    EnrichmentPipeline,
)
from job_search_automation.intelligence.final_selector import (
    FinalSelectionEngine,
)
from job_search_automation.intelligence.resume_matcher import (
    ResumeMatcher,
)
from job_search_automation.models.job import Job
from job_search_automation.models.response import (
    SearchResponse,
)
from job_search_automation.orchestrators.search_orchestrator import (
    SearchOrchestrator,
)
from job_search_automation.pipeline.unique_jobs_export_stage import (
    UniqueJobsExportStage,
)
from job_search_automation.services import logger
from job_search_automation.services.google_sheets import (
    GoogleSheetsService,
)
from job_search_automation.services.google_sheets.application_queue_service import (
    ApplicationQueueSheetsService,
)
from job_search_automation.services.google_sheets.mapper import (
    HEADERS,
    job_to_row,
)
from job_search_automation.utils.deduplication import (
    deduplicate_jobs,
)
from job_search_automation.utils.freshness import (
    apply_freshness_filter,
)


class SearchPipeline:
    """
    End-to-end job search pipeline.

    Flow
    ----
        Search Orchestrator
                ↓
          Deduplication
                ↓
        Unique Jobs Export
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
        Final Jobs Export
                ↓
       Application Workflow
                ↓
       Application Queue Export
                ↓
          SearchResponse

    Responsibilities
    ----------------
    SearchPipeline is responsible only for orchestration.

    It does not:
        • search providers directly
        • perform deduplication itself
        • implement freshness rules
        • implement enrichment rules
        • implement resume scoring
        • implement Gemini logic
        • implement Google Sheets mapping
        • implement application-readiness rules
        • submit applications
    """

    def __init__(self) -> None:
        # ------------------------------------------------------
        # Core search pipeline
        # ------------------------------------------------------

        self.search_orchestrator = SearchOrchestrator()

        self.resume_matcher = ResumeMatcher()

        self.enrichment_pipeline = EnrichmentPipeline()

        self.final_selector = FinalSelectionEngine()

        # ------------------------------------------------------
        # Google Sheets
        # ------------------------------------------------------

        self.google_sheets = GoogleSheetsService()

        # ------------------------------------------------------
        # Unique Jobs export
        # ------------------------------------------------------

        self.unique_jobs_export_stage = UniqueJobsExportStage(
            sheets_service=self.google_sheets,
        )

        # ------------------------------------------------------
        # Application Queue export
        # ------------------------------------------------------
        #
        # This is the production handoff boundary:
        #
        # FinalSelectionEngine
        #        ↓
        # ApplicationWorkflow
        #        ↓
        # ApplicationQueueSheetsExporter
        #        ↓
        # GoogleSheetsService
        #
        # No external application submission occurs here.

        self.application_queue_exporter = (
            ApplicationQueueSheetsService(
                sheets_service=self.google_sheets,
            )
        )

        self.application_workflow = ApplicationWorkflow(
            sheets_exporter=self.application_queue_exporter,
        )

    # ==========================================================
    # PUBLIC ENTRYPOINT
    # ==========================================================

    def run(self) -> SearchResponse:
        """
        Execute the complete job-search pipeline.
        """

        logger.info(
            "Starting search pipeline."
        )

        # ------------------------------------------------------
        # STEP 1 - COLLECTION
        # ------------------------------------------------------

        logger.info(
            "STEP 1 - Collecting jobs"
        )

        jobs = self.search_orchestrator.collect_jobs()

        logger.info(
            "Collected %d jobs.",
            len(jobs),
        )

        # ------------------------------------------------------
        # STEP 2 - DEDUPLICATION
        # ------------------------------------------------------

        logger.info(
            "STEP 2 - Deduplicating"
        )

        jobs = deduplicate_jobs(
            jobs
        )

        logger.info(
            "%d jobs remain after deduplication.",
            len(jobs),
        )

        # ------------------------------------------------------
        # STEP 2A - UNIQUE JOB EXPORT
        # ------------------------------------------------------

        logger.info(
            "STEP 2A - Exporting unique jobs"
        )

        unique_jobs_exported = (
            self.unique_jobs_export_stage.export(
                jobs
            )
        )

        logger.info(
            "%d unique jobs exported.",
            unique_jobs_exported,
        )

        # ------------------------------------------------------
        # STEP 3 - FRESHNESS
        # ------------------------------------------------------

        logger.info(
            "STEP 3 - Freshness"
        )

        jobs = apply_freshness_filter(
            jobs
        )

        logger.info(
            "%d jobs remain after freshness filtering.",
            len(jobs),
        )

        # ------------------------------------------------------
        # STEP 4 - ENRICHMENT + RESUME MATCHING
        # ------------------------------------------------------

        logger.info(
            "STEP 4 - Enrichment + Resume Matching"
        )

        evaluated_jobs: List[Job] = []

        for job in jobs:

            try:
                # Deterministic enrichment
                job = self.enrichment_pipeline.process(
                    job
                )

                # ResumeMatcher performs:
                #   • deterministic matching
                #   • scoring
                #   • Job metadata persistence
                #   • Gemini enrichment
                self.resume_matcher.evaluate(
                    job
                )

                evaluated_jobs.append(
                    job
                )

            except Exception:
                logger.exception(
                    "Job evaluation failed for '%s' at '%s'.",
                    getattr(job, "title", ""),
                    getattr(job, "company", ""),
                )

        logger.info(
            "%d jobs successfully evaluated.",
            len(evaluated_jobs),
        )

        # ------------------------------------------------------
        # STEP 5 - RANKING
        # ------------------------------------------------------

        logger.info(
            "STEP 5 - Ranking jobs"
        )

        evaluated_jobs.sort(
            key=lambda job: (
                job.overall_score or 0,
                job.posting_priority,
            ),
            reverse=True,
        )

        # ------------------------------------------------------
        # STEP 6 - FINAL SELECTION
        # ------------------------------------------------------

        logger.info(
            "STEP 6 - Final Selection"
        )

        selected_jobs = self.final_selector.select(
            evaluated_jobs
        )

        logger.info(
            "Final selection: %d/%d jobs eligible.",
            len(selected_jobs),
            len(evaluated_jobs),
        )

        logger.info("=" * 70)
        logger.info("FINAL SELECTION DECISION REPORT")
        logger.info("=" * 70)

        for job in evaluated_jobs:
            logger.info(
                "TITLE='%s' | COMPANY='%s' | LOCATION='%s' | "
                "SCORE=%.2f | ELIGIBLE=%s | BUCKET='%s' | REASON='%s'",
                job.title,
                job.company,
                job.location,
                job.overall_score or 0.0,
                job.final_selection_eligible,
                job.final_selection_bucket,
                job.final_selection_reason,
            )

        logger.info("=" * 70)

        self._log_selection_report(
            evaluated_jobs,
            selected_jobs,
        )

        # ------------------------------------------------------
        # STEP 7 - FINAL JOBS GOOGLE SHEETS EXPORT
        # ------------------------------------------------------

        logger.info(
            "STEP 7 - Google Sheets Final Jobs Export"
        )

        rows = [
            job_to_row(job)
            for job in selected_jobs
        ]

        self.google_sheets.append_jobs(
            headers=HEADERS,
            rows=rows,
        )

        logger.info(
            "%d jobs exported to Final Jobs worksheet.",
            len(selected_jobs),
        )

        # ------------------------------------------------------
        # STEP 8 - APPLICATION WORKFLOW HANDOFF
        # ------------------------------------------------------

        logger.info(
            "STEP 8 - Application Workflow"
        )

        application_result = (
            self.application_workflow.process(
                selected_jobs,
                export_to_sheets=True,
            )
        )

        logger.info(
            (
                "Application workflow completed | "
                "evaluated=%d | queued=%d | "
                "manual_review=%d | rejected=%d"
            ),
            application_result.evaluated,
            application_result.queued,
            application_result.manual_review,
            application_result.rejected,
        )

        # ------------------------------------------------------
        # COMPLETE
        # ------------------------------------------------------

        logger.info(
            "Search pipeline completed successfully."
        )

        return self._build_response(
            selected_jobs
        )

    # ==========================================================
    # SELECTION REPORT
    # ==========================================================

    @staticmethod
    def _log_selection_report(
        evaluated_jobs: List[Job],
        selected_jobs: List[Job],
    ) -> None:
        """
        Log a concise deterministic final-selection report.
        """

        logger.info(
            "======================================================================"
        )

        logger.info(
            "FINAL SELECTION REPORT"
        )

        logger.info(
            "======================================================================"
        )

        logger.info(
            "Evaluated jobs : %d",
            len(evaluated_jobs),
        )

        logger.info(
            "Selected jobs  : %d",
            len(selected_jobs),
        )

        rejected_jobs = [
            job
            for job in evaluated_jobs
            if not job.final_selection_eligible
        ]

        logger.info(
            "Rejected jobs  : %d",
            len(rejected_jobs),
        )

        bucket_counts: dict[str, int] = {}

        for job in selected_jobs:
            bucket = (
                job.final_selection_bucket
                or "Unknown"
            )

            bucket_counts[bucket] = (
                bucket_counts.get(bucket, 0) + 1
            )

        for bucket, count in sorted(
            bucket_counts.items()
        ):
            logger.info(
                "Bucket %-15s %d jobs",
                bucket,
                count,
            )

        logger.info(
            "----------------------------------------------------------------------"
        )

        for job in selected_jobs:
            logger.info(
                "SELECTED | %-45s | %-25s | Score=%s | Bucket=%s",
                job.title[:45],
                job.company[:25],
                (
                    f"{job.overall_score:.2f}"
                    if job.overall_score is not None
                    else "N/A"
                ),
                job.final_selection_bucket,
            )

        logger.info(
            "======================================================================"
        )

    # ==========================================================
    # RESPONSE BUILDER
    # ==========================================================

    @staticmethod
    def _build_response(
        jobs: List[Job],
    ) -> SearchResponse:
        """
        Convert final selected jobs into the canonical
        SearchResponse object.
        """

        return SearchResponse(
            provider="Pipeline",
            jobs=jobs,
            total_found=len(jobs),
            total_returned=len(jobs),
            success=True,
            message="Pipeline completed successfully.",
        )