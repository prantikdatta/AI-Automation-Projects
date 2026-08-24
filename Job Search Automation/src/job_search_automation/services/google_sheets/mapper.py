from __future__ import annotations

from typing import List

from job_search_automation.models.job import Job


HEADERS = [

    "Run Date",

    "Role",

    "Company",

    "Location",

    "Posted",

    "Score",

    "Bucket",

    "Priority",

    "Recommendation",

    "Matched Skills",

    "Missing Skills",

    "Company Tier",

    "Job Bucket",

    "Blunt Reason",

    "Resume Tailored",

    "Application Status",

    "Job URL",

]


def job_to_row(
    job: Job,
) -> List[str]:

    return [

        str(job.run_date),

        job.title,

        job.company,

        job.location,

        str(job.posted_at),

        str(job.shortlist_likelihood_score),

        job.shortlist_bucket or "",

        str(job.apply_priority),

        job.recommendation or "",

        ", ".join(job.matched_skills),

        ", ".join(job.missing_skills),

        job.company_tier or "",

        job.job_bucket or "",

        job.blunt_reason or "",

        "Yes" if job.tailored_resume_text else "No",

        job.application_status,

        job.job_url,

    ]