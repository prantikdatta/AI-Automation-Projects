from __future__ import annotations

import asyncio

from job_search_automation.ats.factory import ATSFactory
from job_search_automation.ats.registry import ATSRegistry


async def main():

    provider = ATSFactory.greenhouse()

    board = ATSRegistry.boards("greenhouse")[0]

    jobs = await provider.fetch_jobs(board)

    job = jobs[0]

    print()

    print(job.title)

    print()

    print("Description Length")

    print(len(job.description))

    print()

    print(job.description[:1000])


if __name__ == "__main__":

    asyncio.run(main())