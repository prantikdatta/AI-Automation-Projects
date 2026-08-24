from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import List

from job_search_automation.models.job import Job


MAX_JOB_AGE_DAYS = 14


def apply_freshness_filter(
    jobs: List[Job],
) -> List[Job]:
    """
    Removes jobs older than MAX_JOB_AGE_DAYS.

    Priority assignment is handled separately by
    PostingPriority.

    This utility performs filtering only.
    """

    now = datetime.now(
        timezone.utc,
    )

    filtered_jobs: List[Job] = []

    for job in jobs:

        if job.posted_at is None:

            filtered_jobs.append(job)

            continue

        posted_at = job.posted_at

        if posted_at.tzinfo is None:

            posted_at = posted_at.replace(
                tzinfo=timezone.utc,
            )

        age = now - posted_at

        if age <= timedelta(
            days=MAX_JOB_AGE_DAYS,
        ):

            filtered_jobs.append(job)

    return filtered_jobs