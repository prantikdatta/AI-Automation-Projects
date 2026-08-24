import asyncio


from job_search_automation.ats.orchestrator import (
    ATSOrchestrator,
)



async def main():

    orchestrator = (
        ATSOrchestrator.create()
    )


    jobs = await orchestrator.run()


    print(
        f"Total ATS jobs: {len(jobs)}"
    )


    providers = {}


    for job in jobs:

        providers[job.provider] = (
            providers.get(
                job.provider,
                0
            )
            + 1
        )


    print(
        providers
    )


    for job in jobs[:10]:

        print("-" * 50)

        print(
            job.title
        )

        print(
            job.company
        )

        print(
            job.provider
        )


if __name__ == "__main__":

    asyncio.run(main())