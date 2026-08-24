from __future__ import annotations

from datetime import timezone

from job_search_automation.models.job import Job
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)

from job_search_automation.utils.company_tier import (
    CompanyTierClassifier,
)

from job_search_automation.utils.job_bucket_classifier import (
    JobBucketClassifier,
)

from job_search_automation.utils.location_normalizer import (
    LocationNormalizer,
)

from job_search_automation.utils.posting_priority import (
    PostingPriority,
)

from job_search_automation.utils.salary_normalizer import (
    SalaryNormalizer,
)

from job_search_automation.utils.seniority_classifier import (
    SeniorityClassifier,
)

from job_search_automation.utils.skill_extractor import (
    SkillExtractor,
)

from job_search_automation.utils.work_mode_classifier import (
    WorkModeClassifier,
)


class CanonicalMapper:
    """
    Converts a provider-independent NormalizedJob
    into the project's canonical Job model.
    """

    @staticmethod
    def to_job(
        normalized: NormalizedJob,
    ) -> Job:

        posted_at = normalized.posted_at

        if (
            posted_at is not None
            and posted_at.tzinfo is None
        ):
            posted_at = posted_at.replace(
                tzinfo=timezone.utc,
            )

        salary_min = normalized.salary_min
        salary_max = normalized.salary_max
        currency = normalized.currency

        #
        # Ashby salary extraction
        #
        if (
            normalized.provider == "Ashby"
            and normalized.raw.get("compensation")
        ):

            summary = normalized.raw["compensation"].get(
                "summaryComponents",
                [],
            )

            for component in summary:

                if component.get("compensationType") == "Salary":

                    salary_min = component.get("minValue")
                    salary_max = component.get("maxValue")
                    currency = component.get("currencyCode")
                    break

        (
            salary_min,
            salary_max,
            currency,
            salary_confidence,
        ) = SalaryNormalizer.normalize(
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            description=normalized.description,
        )

        location = LocationNormalizer.normalize(
            normalized.location,
        )

        company_tier = CompanyTierClassifier.classify(
            normalized.company,
        )

        work_mode = WorkModeClassifier.classify(
            location,
            normalized.work_mode,
            normalized.remote,
        )

        job_bucket = JobBucketClassifier.classify(
            normalized.title,
            normalized.description,
        )

        seniority = SeniorityClassifier.classify(
            normalized.title,
            normalized.description,
        )

        posting_priority = PostingPriority.classify(
            posted_at,
        )

        skills = (
            normalized.skills
            if normalized.skills
            else SkillExtractor.extract(
                normalized.description,
            )
        )

        return Job(
            searched_role=normalized.searched_role,
            title=normalized.title,
            company=normalized.company,
            company_tier=company_tier,
            location=location,
            description=normalized.description,
            job_url=normalized.job_url,
            provider=normalized.provider,
            source=normalized.source,
            posted_at=posted_at,
            posting_priority=posting_priority,
            employment_type=normalized.employment_type,
            seniority=seniority,
            remote=normalized.remote,
            work_mode=work_mode,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            salary_confidence=salary_confidence,
            job_bucket=job_bucket,
            skills=skills,
            raw=normalized.raw,
        )