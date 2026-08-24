from __future__ import annotations

import asyncio

from job_search_automation.ats.orchestrator import (
    ATSOrchestrator,
)


async def main():

    orchestrator = ATSOrchestrator.create()

    jobs = await orchestrator.run()

    print(
        f"\nTotal jobs fetched: {len(jobs)}\n"
    )

    for index, job in enumerate(
        jobs[:5],
        start=1,
    ):

        print("=" * 100)

        print(
            f"JOB #{index}"
        )

        print("=" * 100)

        print(
            f"Title       : {job.title}"
        )

        print(
            f"Company     : {job.company}"
        )

        print(
            f"Location    : {job.location}"
        )

        print(
            f"Provider    : {job.provider}"
        )

        print(
            f"Source      : {job.source}"
        )

        print(
            f"URL         : {job.job_url}"
        )

        print(
            f"Posted At   : {job.posted_at}"
        )

        print()

        print(
            f"Description Length : {len(job.description or '')}"
        )

        print()

        print(
            "Skills:"
        )

        print(
            job.skills
        )

        print()

        print(
            "Description Preview:"
        )

        print(
            (job.description or "")[:800]
        )

        print("\n")


if __name__ == "__main__":

    asyncio.run(main())