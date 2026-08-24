import asyncio

from job_search_automation.ats.lever.client import (
    LeverClient,
)


async def main():

    client = LeverClient()

    response = await client.client.get(
        "https://api.lever.co/v0/postings/netflix",
        params={
            "mode": "json"
        },
    )

    print("STATUS:")
    print(response.status_code)

    print("\nHEADERS:")
    print(response.headers)

    print("\nBODY:")
    print(response.text[:500])

    await client.close()


asyncio.run(main())