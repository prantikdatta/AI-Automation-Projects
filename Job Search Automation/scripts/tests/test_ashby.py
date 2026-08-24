import asyncio

from job_search_automation.ats.ashby.client import (
    AshbyClient,
)


async def main():

    client = AshbyClient()

    response = await client.client.get(
        "https://jobs.ashbyhq.com/api/non-user-application/openai"
    )

    print("STATUS:")
    print(response.status_code)

    print()

    print(response.text[:500])

    await client.close()


asyncio.run(main())