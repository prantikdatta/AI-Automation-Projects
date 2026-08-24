from __future__ import annotations

import re
from typing import Iterable, List, Set

from job_search_automation.config.resume_strategy import (
    CORE_SKILLS,
    PREFERRED_SKILLS,
)
from job_search_automation.config.skill_dictionary import (
    SKILL_ALIASES,
)
from job_search_automation.intelligence.models import (
    SkillMatchResult,
)


class SkillMatcher:
    """
    Deterministic skill matching engine.

    Responsibilities
    ----------------
    - Normalize resume skills
    - Normalize job skills
    - Compute overlap
    - Return SkillMatchResult
    """

    def __init__(self) -> None:

        resume_skills = list(CORE_SKILLS) + list(PREFERRED_SKILLS)

        self.resume_skills = self._normalize_skills(
            resume_skills
        )

    def match(
        self,
        job_skills: List[str],
    ) -> SkillMatchResult:

        normalized_job_skills = self._normalize_skills(
            job_skills
        )

        matched = sorted(
            self.resume_skills.intersection(
                normalized_job_skills
            )
        )

        missing = sorted(
            normalized_job_skills.difference(
                self.resume_skills
            )
        )

        if not normalized_job_skills:

            score = 0.0

            explanation = (
                "No identifiable skills were extracted "
                "from the job description."
            )

        else:

            score = (
                len(matched)
                / len(normalized_job_skills)
            ) * 100

            if matched:

                explanation = (
                    f"Matched {len(matched)} of "
                    f"{len(normalized_job_skills)} required skills."
                )

                if missing:

                    explanation += (
                        f" Missing skills: "
                        f"{', '.join(missing)}."
                    )

            else:

                explanation = (
                    "No overlap between resume skills "
                    "and job requirements."
                )

        return SkillMatchResult(

            score=round(score, 2),

            matched_skills=matched,

            missing_skills=missing,

            explanation=explanation,

            confidence=1.0,

            metadata={

                "resume_skill_count": len(
                    self.resume_skills
                ),

                "job_skill_count": len(
                    normalized_job_skills
                ),

                "matched_skill_count": len(
                    matched
                ),

                "missing_skill_count": len(
                    missing
                ),

            },

        )

    def _normalize_skills(
        self,
        skills: Iterable[str],
    ) -> Set[str]:

        normalized = set()

        for skill in skills:

            skill = skill.strip().lower()

            skill = re.sub(
                r"\s+",
                " ",
                skill,
            )

            canonical = SKILL_ALIASES.get(
                skill,
                skill,
            )

            normalized.add(canonical)

        return normalized