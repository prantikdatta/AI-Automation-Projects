import asyncio


from job_search_automation.sources.orchestrator import (
    JobSourceOrchestrator,
)



async def main():

    orchestrator = (
        JobSourceOrchestrator.create()
    )


    jobs = await orchestrator.run()


    print(
        f"Total jobs: {len(jobs)}"
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