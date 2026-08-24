from __future__ import annotations

from job_search_automation.models.job import Job

from .skill_extractor import SkillExtractor
from .role_classifier import RoleClassifier


class EnrichmentPipeline:
    """
    Orchestrates deterministic job enrichment.

    Flow:

    Job
     |
     ├── Skill Extraction
     |
     ├── Role Classification
     |
     └── Scoring
     |
     ↓
    Enriched Job
    """

    @classmethod
    def process(
        cls,
        job: Job,
    ) -> Job:
        """
        Execute complete enrichment pipeline.
        """

        job = SkillExtractor.extract(
            job
        )

        job = RoleClassifier.classify(
            job
        )

        return job