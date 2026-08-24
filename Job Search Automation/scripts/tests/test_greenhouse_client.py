import asyncio

from job_search_automation.ats.greenhouse.client import (
    GreenhouseClient,
)


async def main():

    client = GreenhouseClient()

    jobs = await client.get_jobs("stripe")

    print("Type:", type(jobs))

    print("Count:", len(jobs))

    print("First Item Type:", type(jobs[0]))

    print()

    print(jobs[0])

    await client.close()


if __name__ == "__main__":

    asyncio.run(main())