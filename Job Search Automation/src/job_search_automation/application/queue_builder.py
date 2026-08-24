from __future__ import annotations

from typing import Iterable

from job_search_automation.application.decision import (
    ApplicationReadinessResult,
)
from job_search_automation.application.queue import (
    ApplicationQueueEngine,
    ApplicationQueueItem,
)
from job_search_automation.application.readiness import (
    ApplicationReadinessEngine,
)
from job_search_automation.models.job import Job


class ApplicationQueueBuilder:
    """
    Compatibility wrapper around the existing ApplicationQueueEngine.

    ApplicationQueueEngine is the authoritative queue-state builder.
    """

    def __init__(
        self,
        readiness_engine: ApplicationReadinessEngine | None = None,
    ) -> None:
        self.readiness_engine = (
            readiness_engine
            or ApplicationReadinessEngine()
        )
        self.queue_engine = ApplicationQueueEngine()

    def build(
        self,
        jobs: Iterable[Job],
    ) -> list[ApplicationQueueItem]:
        queue: list[ApplicationQueueItem] = []

        for job in jobs:
            readiness = self.readiness_engine.evaluate(job)

            if not readiness.eligible:
                continue

            queue.append(
                self.queue_engine.build(
                    job,
                    readiness,
                )
            )

        return queue

    def build_one(
        self,
        job: Job,
    ) -> ApplicationQueueItem | None:
        readiness: ApplicationReadinessResult = (
            self.readiness_engine.evaluate(job)
        )

        if not readiness.eligible:
            return None

        return self.queue_engine.build(
            job,
            readiness,
        )