from __future__ import annotations

import asyncio

from job_search_automation.ats.factory import ATSFactory
from job_search_automation.ats.registry import ATSRegistry
from job_search_automation.matching.rule_matcher import RuleMatcher
from job_search_automation.utils.skill_extractor import SkillExtractor


async def main():

    provider = ATSFactory.greenhouse()

    matcher = RuleMatcher()

    boards = ATSRegistry.boards("greenhouse")

    total = 0

    for board in boards:

        jobs = await provider.fetch_jobs(board)

        for job in jobs:

            job.skills = SkillExtractor.extract(
                job.description
            )

            result = await matcher.match(job)

            if result.recommendation == "Skip":

                continue

            total += 1

            print("=" * 100)

            print(job.title)

            print(job.company)

            print(job.location)

            print()

            print(result.score)

            print(result.recommendation)

            print(result.matched_skills)

            print()

            if total == 20:

                return


if __name__ == "__main__":

    asyncio.run(main())