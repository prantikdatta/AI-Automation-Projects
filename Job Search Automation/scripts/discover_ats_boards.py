import asyncio


from job_search_automation.ats.factory import (
    ATSFactory,
)

from job_search_automation.ats.registry import (
    ATSRegistry,
)


async def main():


    providers = {

        "greenhouse":
            ATSFactory.greenhouse(),

        "lever":
            ATSFactory.lever(),

        "ashby":
            ATSFactory.ashby(),

    }


    for ats, provider in providers.items():

        print("\n")
        print("=" * 50)
        print(
            ats.upper()
        )


        boards = ATSRegistry.boards(
            ats
        )


        for board in boards:


            jobs = await provider.client.get_jobs(
                board.board
            )


            print(

                board.company,

                board.board,

                len(jobs)

            )



asyncio.run(main())