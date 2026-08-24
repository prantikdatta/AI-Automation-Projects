from __future__ import annotations

import re

from job_search_automation.skills.skill_dictionary import (
    SKILLS,
)


class SkillExtractor:

    @staticmethod
    def extract(
        description: str,
    ) -> list[str]:

        if not description:

            return []

        text = description.lower()

        skills = []

        for skill in SKILLS:

            pattern = (
                r"\b"
                + re.escape(skill.lower())
                + r"\b"
            )

            if re.search(
                pattern,
                text,
            ):

                skills.append(
                    skill.title()
                )

        return sorted(

            set(skills)

        )