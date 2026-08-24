from __future__ import annotations

from datetime import datetime
from typing import Any

from job_search_automation.normalizers.base import BaseNormalizer
from job_search_automation.normalizers.normalized_job import (
    NormalizedJob,
)


class RapidAPINormalizer(BaseNormalizer):

    provider_name = "RapidAPI"


    def normalize(
        self,
        raw: dict[str, Any],
        searched_role: str,
    ) -> NormalizedJob:

        posted_at = None


        posted = (
            raw.get("job_posted_at_datetime_utc")
            or raw.get("job_posted_at_datetime")
        )


        if posted:

            try:

                posted_at = datetime.fromisoformat(
                    posted.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except Exception:

                posted_at = None



        salary_min = raw.get(
            "job_min_salary"
        )


        salary_max = raw.get(
            "job_max_salary"
        )


        currency = raw.get(
            "job_salary_currency"
        )



        remote = (
            raw.get(
                "job_is_remote"
            )
            or False
        )



        work_mode = (
            "Remote"
            if remote
            else "Onsite"
        )



        employment_type = (

            raw.get(
                "job_employment_type"
            )

            if raw.get(
                "job_employment_type"
            )

            else None

        )



        description = raw.get(
            "job_description",
            "",
        )



        location = (

            raw.get(
                "job_location"
            )

            or ", ".join(

                filter(

                    None,

                    [

                        raw.get(
                            "job_city"
                        ),

                        raw.get(
                            "job_state"
                        ),

                        raw.get(
                            "job_country"
                        ),

                    ],

                )

            )

        )



        return NormalizedJob(

            searched_role=searched_role,


            title=raw.get(
                "job_title",
                "",
            ),


            company=raw.get(
                "employer_name",
                "",
            ),


            location=location,


            description=description,


            job_url=raw.get(
                "job_apply_link",
                "",
            ),


            provider=self.provider_name,


            source=self.provider_name,


            posted_at=posted_at,


            employment_type=employment_type,


            seniority=raw.get(
                "job_required_experience",
            ),


            remote=remote,


            work_mode=work_mode,


            salary_min=salary_min,


            salary_max=salary_max,


            currency=currency,


            salary_confidence=(

                1.0

                if salary_min or salary_max

                else None

            ),


            skills=[],


            raw=raw,

        )