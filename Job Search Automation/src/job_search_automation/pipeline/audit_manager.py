from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from job_search_automation.models.job import Job
from job_search_automation.models.pipeline_audit import (
    JobPipelineAudit,
    PipelineStage,
    PipelineStatus,
)


class PipelineAuditManager:
    """
    Maintains one JobPipelineAudit per job for a pipeline run.
    """

    def __init__(
        self,
        run_id: str | None = None,
    ) -> None:
        self.run_id = (
            run_id
            or str(uuid4())
        )

        self.audits: dict[
            str,
            JobPipelineAudit,
        ] = {}

    def create(
        self,
        job: Job,
    ) -> JobPipelineAudit:
        job_id = self._job_id(job)

        audit = self.audits.get(job_id)

        if audit is not None:
            return audit

        audit = JobPipelineAudit(
            job_id=job_id,
            source=job.source,
            company=job.company,
            title=job.title,
            location=job.location,
            job_url=job.job_url,
            posted_at=job.posted_at,
            run_id=self.run_id,
            searched_role=job.searched_role,
        )

        self.audits[job_id] = audit

        return audit

    def get(
        self,
        job: Job,
    ) -> JobPipelineAudit:
        return self.create(job)

    def record(
        self,
        job: Job,
        stage: PipelineStage,
        status: PipelineStatus,
        reason: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> JobPipelineAudit:
        audit = self.get(job)

        audit.record(
            stage=stage,
            status=status,
            reason=reason,
            metadata=metadata,
        )

        return audit

    def record_pass(
        self,
        job: Job,
        stage: PipelineStage,
        reason: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> JobPipelineAudit:
        return self.record(
            job=job,
            stage=stage,
            status=PipelineStatus.PASSED,
            reason=reason,
            metadata=metadata,
        )

    def record_rejection(
        self,
        job: Job,
        stage: PipelineStage,
        reason: str,
        metadata: dict[str, object] | None = None,
    ) -> JobPipelineAudit:
        return self.record(
            job=job,
            stage=stage,
            status=PipelineStatus.REJECTED,
            reason=reason,
            metadata=metadata,
        )

    def record_duplicate(
        self,
        job: Job,
        reason: str,
        metadata: dict[str, object] | None = None,
    ) -> JobPipelineAudit:
        return self.record(
            job=job,
            stage=PipelineStage.DEDUPLICATION,
            status=PipelineStatus.DUPLICATE,
            reason=reason,
            metadata=metadata,
        )

    def record_metadata(
        self,
        job: Job,
        stage: PipelineStage,
        metadata: dict[str, object],
        status: PipelineStatus = PipelineStatus.PASSED,
        reason: str | None = None,
    ) -> JobPipelineAudit:
        return self.record(
            job=job,
            stage=stage,
            status=status,
            reason=reason,
            metadata=metadata,
        )

    def all_audits(
        self,
    ) -> list[JobPipelineAudit]:
        return list(
            self.audits.values()
        )

    def for_jobs(
        self,
        jobs: list[Job],
    ) -> list[JobPipelineAudit]:
        return [
            self.get(job)
            for job in jobs
        ]

    @staticmethod
    def _job_id(
        job: Job,
    ) -> str:
        if job.job_url:
            return job.job_url.strip().lower()

        return "|".join(
            [
                job.company.strip().lower(),
                job.title.strip().lower(),
                job.location.strip().lower(),
            ]
        )