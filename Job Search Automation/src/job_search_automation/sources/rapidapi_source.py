from __future__ import annotations


from job_search_automation.providers.provider_registry import (
    RapidAPIProvider,
)

from job_search_automation.models.request import (
    SearchRequest,
)


class RapidAPISource:
    """
    Adapter converting RapidAPIProvider
    into unified job source interface.

    Output:
        list[Job]
    """


    def __init__(self):

        self.provider = RapidAPIProvider()



    async def fetch_jobs(self):

        roles = [

            "data analyst",

            "business analyst",

            "product analyst",

            "business intelligence analyst",

            "analytics consultant",

        ]


        locations = [

            "Mumbai",

            "Bangalore",

            "Hyderabad",

            "Remote",

            "India",

        ]


        jobs = []


        for role in roles:


            request = SearchRequest(

                searched_role=role,

                keywords=[

                    role,

                    "analytics",

                    "SQL",

                    "Power BI",

                    "Python",

                ],

                locations=locations,

            )


            response = self.provider.search(
                request
            )


            jobs.extend(
                response.jobs
            )


        return jobs