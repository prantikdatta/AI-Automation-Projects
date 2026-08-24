from __future__ import annotations


class ATSDeduplicator:
    """
    Removes duplicate jobs from ATS sources.
    """


    @staticmethod
    def deduplicate(
        jobs: list,
    ) -> list:

        seen = set()

        unique_jobs = []


        for job in jobs:

            key = (
                job.company,
                job.title,
                job.location,
            )


            if key in seen:
                continue


            seen.add(key)

            unique_jobs.append(
                job
            )


        return unique_jobs