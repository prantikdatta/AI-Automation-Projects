from __future__ import annotations

from job_search_automation.config.resume_strategy import (
    CANDIDATE_YEARS_EXPERIENCE,
)
from job_search_automation.config.scoring_rules import (
    EXPERIENCE_SCORE,
)
from job_search_automation.intelligence.models import (
    ExperienceMatchResult,
)
from job_search_automation.utils.experience_parser import (
    ExperienceParser,
)


class ExperienceMatcher:
    """
    Determines how well the candidate's experience
    aligns with the job requirement.
    """

    def __init__(self) -> None:

        self.candidate_years = (
            CANDIDATE_YEARS_EXPERIENCE
        )

    def match(
        self,
        job_description: str,
    ) -> ExperienceMatchResult:

        required = ExperienceParser.parse(
            job_description
        )

        if required is None:

            return ExperienceMatchResult(

                score=EXPERIENCE_SCORE[
                    "experience_not_found"
                ],

                required_years=None,

                candidate_years=self.candidate_years,

                experience_gap=None,

                explanation=(
                    "Experience requirement was not "
                    "identified in the job description."
                ),

                confidence=0.5,

                metadata={
                    "experience_found": False,
                },

            )

        gap = self.candidate_years - required

        if gap >= 2:

            score = EXPERIENCE_SCORE[
                "gap_greater_equal_2"
            ]

            explanation = (
                "Candidate exceeds the required "
                "experience by at least two years."
            )

        elif gap >= 0:

            score = EXPERIENCE_SCORE[
                "gap_greater_equal_0"
            ]

            explanation = (
                "Candidate meets the required "
                "experience."
            )

        elif gap >= -1:

            score = EXPERIENCE_SCORE[
                "gap_greater_equal_minus_1"
            ]

            explanation = (
                "Candidate is slightly below the "
                "required experience."
            )

        elif gap >= -2:

            score = EXPERIENCE_SCORE[
                "gap_greater_equal_minus_2"
            ]

            explanation = (
                "Candidate is moderately below the "
                "required experience."
            )

        else:

            score = EXPERIENCE_SCORE[
                "gap_less_minus_2"
            ]

            explanation = (
                "Candidate falls well below the "
                "required experience."
            )

        return ExperienceMatchResult(

            score=score,

            required_years=required,

            candidate_years=self.candidate_years,

            experience_gap=round(
                gap,
                2,
            ),

            explanation=explanation,

            confidence=1.0,

            metadata={

                "experience_found": True,

                "required_years": required,

                "candidate_years": self.candidate_years,

                "experience_gap": round(
                    gap,
                    2,
                ),

            },

        )