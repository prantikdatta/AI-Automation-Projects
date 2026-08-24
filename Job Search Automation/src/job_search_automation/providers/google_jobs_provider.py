from job_search_automation.clients.google_jobs_client import GoogleJobsClient
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest
from job_search_automation.models.response import SearchResponse
from job_search_automation.providers.base import BaseProvider


class GoogleJobsProvider(BaseProvider):

    name = "GoogleJobs"

    def __init__(self):

        self.client = GoogleJobsClient()

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        response = self.client.search_jobs(
            query=" ".join(request.keywords),
        )

        jobs = []

        for item in response.get("jobs_results", []):

            location = item.get("location") or ""

            jobs.append(

                Job(

                    searched_role=" ".join(request.keywords),

                    title=item.get("title", ""),

                    company=item.get("company_name", ""),

                    location=location,

                    description=item.get("description", ""),

                    job_url=item.get("share_link")
                    or item.get("apply_options", [{}])[0].get("link", "")
                    or "",

                    source="Google Jobs",

                    provider=self.name,

                    employment_type=item.get("detected_extensions", {}).get(
                        "schedule_type"
                    ),

                    seniority=None,

                    remote="remote" in location.lower(),

                    work_mode=(
                        "Remote"
                        if "remote" in location.lower()
                        else "Onsite"
                    ),

                    salary_min=None,

                    salary_max=None,

                    currency=None,

                    skills=[],

                    raw=item,

                )

            )

        return SearchResponse(

            provider=self.name,

            jobs=jobs,

            total_found=len(jobs),

        )