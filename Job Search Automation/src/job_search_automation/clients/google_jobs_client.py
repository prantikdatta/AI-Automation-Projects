from typing import Any, Dict

from serpapi import GoogleSearch

from job_search_automation.config import settings


class GoogleJobsClient:

    def search_jobs(
        self,
        query: str,
    ) -> Dict[str, Any]:

        search = GoogleSearch(

            {

                "engine": "google_jobs",

                "q": query,

                "hl": "en",

                "gl": "in",

                "api_key": settings.SERPAPI_API_KEY,

            }

        )

        return search.get_dict()