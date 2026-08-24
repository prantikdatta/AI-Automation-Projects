from __future__ import annotations

import asyncio

from job_search_automation.ats.greenhouse.detail_client import (
    GreenhouseDetailClient,
)


async def main():

    client = GreenhouseDetailClient()

    job = await client.get_job(

        board="stripe",

        job_id=7739207,

    )

    print(type(job))

    print()

    print(job.keys())

    print()

    print(job)


if __name__ == "__main__":

    asyncio.run(main())