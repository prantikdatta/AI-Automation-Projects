from __future__ import annotations

from job_search_automation.config.current_role import (
    CURRENT_ROLE,
)
from job_search_automation.config.role_hierarchy import (
    ROLE_HIERARCHY,
)
from job_search_automation.config.scoring_rules import (
    CAREER_PROGRESSION_SCORE,
)
from job_search_automation.intelligence.models import (
    CareerProgressionResult,
)


class CareerProgressionMatcher:
    """
    Determines whether a job represents career growth,
    a lateral move, or a downgrade.

    The matcher compares the candidate's current role with
    the detected job title using the configured role hierarchy.
    """

    def __init__(self) -> None:

        self.current_role = CURRENT_ROLE

        self.current_level = ROLE_HIERARCHY.get(
            CURRENT_ROLE.lower(),
            5,
        )

    def match(
        self,
        job_title: str,
    ) -> CareerProgressionResult:

        title = job_title.lower().strip()

        matched_role = None

        matched_level = None

        for role in sorted(
            ROLE_HIERARCHY.keys(),
            key=len,
            reverse=True,
        ):

            if role in title:

                matched_role = role

                matched_level = ROLE_HIERARCHY[role]

                break

        if matched_level is None:

            return CareerProgressionResult(

                score=70,

                current_role=self.current_role,

                matched_role=None,

                current_level=self.current_level,

                job_level=None,

                level_difference=None,

                recommendation="Unknown Role",

                explanation=(
                    "Unable to map the job title to the "
                    "configured career hierarchy."
                ),

                confidence=0.50,

                metadata={
                    "matched": False,
                    "job_title": job_title,
                },

            )

        level_difference = (
            matched_level - self.current_level
        )

        if level_difference >= 3:

            score = CAREER_PROGRESSION_SCORE[
                "promotion"
            ]

            recommendation = "Strong Promotion"

            explanation = (
                "Significant upward career progression."
            )

        elif level_difference >= 1:

            score = CAREER_PROGRESSION_SCORE[
                "ideal_growth"
            ]

            recommendation = "Career Growth"

            explanation = (
                "Logical next career step."
            )

        elif level_difference == 0:

            score = CAREER_PROGRESSION_SCORE[
                "lateral"
            ]

            recommendation = "Lateral Move"

            explanation = (
                "Role is aligned with the current career level."
            )

        elif level_difference == -1:

            score = CAREER_PROGRESSION_SCORE[
                "slight_downgrade"
            ]

            recommendation = "Minor Downgrade"

            explanation = (
                "Slight downgrade from the current role."
            )

        else:

            score = CAREER_PROGRESSION_SCORE[
                "major_downgrade"
            ]

            recommendation = "Career Regression"

            explanation = (
                "Role represents a major career downgrade."
            )

        return CareerProgressionResult(

            score=score,

            current_role=self.current_role,

            matched_role=matched_role,

            current_level=self.current_level,

            job_level=matched_level,

            level_difference=level_difference,

            recommendation=recommendation,

            explanation=explanation,

            confidence=1.0,

            metadata={

                "matched": True,

                "job_title": job_title,

                "matched_role": matched_role,

                "current_level": self.current_level,

                "job_level": matched_level,

                "level_difference": level_difference,

            },

        )