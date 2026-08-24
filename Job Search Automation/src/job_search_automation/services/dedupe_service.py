from __future__ import annotations

from job_search_automation.config.scoring_rules import (
    DUPLICATE_RULES,
)
from job_search_automation.intelligence.deduplication.job_deduplicator import (
    DuplicateDecision,
    JobDeduplicator,
)
from job_search_automation.models.job import Job


class DedupeService:
    """
    Service wrapper around the deterministic JobDeduplicator.

    The service owns configuration and exposes a simple interface
    for pipeline stages.
    """

    def __init__(
        self,
        similarity_threshold: float | None = None,
    ) -> None:
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else float(
                DUPLICATE_RULES[
                    "similarity_threshold"
                ]
            )
        )

        self._deduplicator = JobDeduplicator(
            similarity_threshold=threshold
        )

    def deduplicate(
        self,
        jobs: list[Job],
    ) -> tuple[
        list[Job],
        dict[str, DuplicateDecision],
    ]:
        """
        Return canonical unique jobs and duplicate decisions.
        """

        return self._deduplicator.deduplicate(jobs)