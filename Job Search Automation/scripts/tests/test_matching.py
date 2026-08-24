import asyncio

from job_search_automation.sources.orchestrator import (
    JobSourceOrchestrator,
)

from job_search_automation.matching.orchestrator import (
    MatchOrchestrator,
)


async def main():

    jobs = await (
        JobSourceOrchestrator.create()
    ).run()


    jobs = await (
        MatchOrchestrator()
    ).evaluate(
        jobs
    )


    for job in jobs[:5]:

        print("=" * 60)

        print(job.title)

        print(job.company)

        print(job.shortlist_likelihood_score)

        print(job.matched_skills)

        print(job.missing_skills)


if __name__ == "__main__":

    asyncio.run(main())