from __future__ import annotations

import asyncio

from job_search_automation.ats.orchestrator import (
    ATSOrchestrator,
)

from job_search_automation.ats.filter import (
    ATSJobFilter,
)


async def main():

    orchestrator = ATSOrchestrator.create()

    jobs = await orchestrator.run()

    print(
        f"Before filtering: {len(jobs)}"
    )


    job_filter = ATSJobFilter(

        target_locations=[
            "Mumbai",
            "Bangalore",
            "Bengaluru",
            "Hyderabad",
            "Remote",
            "India",
        ],

        keywords=[

            "data analyst",
            "business analyst",
            "analytics",
            "bi",
            "business intelligence",
            "product analyst",

        ],
    )


    filtered_jobs = job_filter.filter(
        jobs
    )


    print(
        f"After filtering: {len(filtered_jobs)}"
    )


    for job in filtered_jobs[:10]:

        print("-" * 50)

        print(
            f"Title: {job.title}"
        )

        print(
            f"Company: {job.company}"
        )

        print(
            f"Location: {job.location}"
        )

        print(
            f"URL: {job.job_url}"
        )


if __name__ == "__main__":

    asyncio.run(main())