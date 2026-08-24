import asyncio

from job_search_automation.ats.ashby.client import (
    AshbyClient,
)


async def main():

    client = AshbyClient()


    candidates = [

        "openai",
        "cursor",
        "retool",
        "anthropic",
        "ramp",

    ]


    for board in candidates:

        jobs = await client.get_jobs(
            board
        )

        print(
            board,
            "=>",
            len(jobs)
        )


    await client.close()



asyncio.run(main())