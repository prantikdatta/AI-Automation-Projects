from __future__ import annotations

from job_search_automation.matching.base import (
    BaseMatcher,
)

from job_search_automation.matching.models import (
    MatchResult,
)

from job_search_automation.models.job import (
    Job,
)

from job_search_automation.profile.loader import (
    ResumeProfileLoader,
)


class RuleMatcher(BaseMatcher):

    async def match(
        self,
        job: Job,
    ) -> MatchResult:

        profile = ResumeProfileLoader.load()

        resume_skills = {

            skill.lower()

            for skill in profile.skills

        }

        job_skills = {

            skill.lower()

            for skill in (job.skills or [])

        }

        matched = sorted(

            resume_skills.intersection(

                job_skills

            )

        )

        missing = sorted(

            resume_skills.difference(

                job_skills

            )

        )

        if resume_skills:

            skill_score = int(

                len(matched)

                /

                len(resume_skills)

                *

                60

            )

        else:

            skill_score = 0

        role_score = 0

        title = (

            job.title or ""

        ).lower()

        for role in (profile.preferred_roles or []):

            if role.lower() in title:

                role_score = 20

                break

        location_score = 0

        location = (

            job.location or ""

        ).lower()

        for city in (profile.preferred_locations or []):

            if city.lower() in location:

                location_score = 10

                break

        experience_score = 10

        score = min(

            skill_score

            + role_score

            + location_score

            + experience_score,

            100,

        )

        strengths = []

        weaknesses = []

        if matched:

            strengths.append(

                f"{len(matched)} resume skills matched."

            )

        if missing:

            weaknesses.append(

                f"{len(missing)} resume skills missing."

            )

        recommendation = (

            "Apply"

            if score >= 75

            else

            "Review"

            if score >= 50

            else

            "Skip"

        )

        return MatchResult(

            score=score,

            matched_skills=matched,

            missing_skills=missing,

            strengths=strengths,

            weaknesses=weaknesses,

            recommendation=recommendation,

            skill_score=skill_score,

            role_score=role_score,

            location_score=location_score,

            experience_score=experience_score,

        )