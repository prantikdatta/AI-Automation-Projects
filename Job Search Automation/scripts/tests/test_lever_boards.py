import asyncio

from job_search_automation.ats.registry import (
    ATSRegistry,
)

from job_search_automation.ats.lever.client import (
    LeverClient,
)


async def main():

    client = LeverClient()

    boards = ATSRegistry.boards(
        "lever"
    )


    for board in boards:

        jobs = await client.get_jobs(
            board.board
        )

        print(
            board.company,
            board.board,
            len(jobs)
        )


    await client.close()


asyncio.run(main())