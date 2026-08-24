from job_search_automation.models.request import SearchRequest
from job_search_automation.providers.rapidapi_provider import RapidAPIProvider


def main():

    provider = RapidAPIProvider()

    request = SearchRequest(
        keywords=["Data Analyst"],
        locations=["Mumbai"],
        limit=5,
    )

    response = provider.search(request)

    print(f"\nProvider : {response.provider}")
    print(f"Jobs Found : {response.total_found}\n")

    for i, job in enumerate(response.jobs, start=1):

        print("-" * 80)

        print(f"{i}. {job.title}")

        print(f"Company : {job.company}")

        print(f"Location : {job.location}")

        print(f"Remote : {job.remote}")

        print(f"URL : {job.job_url}")

        print()


if __name__ == "__main__":
    main()