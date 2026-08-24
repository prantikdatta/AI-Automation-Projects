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
        f"Ranked jobs: {len(jobs)}"
    )


    for job in jobs:

        print("-" * 60)

        print(
            job.title
        )

        print(
            job.company
        )

        print(
            "Score:",
            job.shortlist_likelihood_score
        )



if __name__ == "__main__":

    asyncio.run(main())