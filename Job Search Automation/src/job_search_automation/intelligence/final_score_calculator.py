from __future__ import annotations

from job_search_automation.config.final.score_weights import (
    FINAL_SCORE_WEIGHTS,
    TOTAL_WEIGHT,
)
from job_search_automation.intelligence.models import (
    CareerProgressionResult,
    CompanyScoreResult,
    ExperienceMatchResult,
    FinalScoreResult,
    FreshnessScoreResult,
    LocationMatchResult,
    SkillMatchResult,
)
from job_search_automation.intelligence.utils.score_bucket import (
    ScoreBucket,
)


class FinalScoreCalculator:
    """
    Calculates the final deterministic score and converts it
    into a recommendation consumed by downstream components.
    """

    def __init__(self) -> None:
        self.bucket = ScoreBucket()

    def calculate(
        self,
        skill_result: SkillMatchResult,
        experience_result: ExperienceMatchResult,
        career_result: CareerProgressionResult,
        location_result: LocationMatchResult,
        company_result: CompanyScoreResult,
        freshness_result: FreshnessScoreResult,
    ) -> FinalScoreResult:
        weighted_score = (
            skill_result.score
            * FINAL_SCORE_WEIGHTS["skills"]
            + experience_result.score
            * FINAL_SCORE_WEIGHTS["experience"]
            + career_result.score
            * FINAL_SCORE_WEIGHTS["career"]
            + location_result.score
            * FINAL_SCORE_WEIGHTS["location"]
            + company_result.score
            * FINAL_SCORE_WEIGHTS["company"]
            + freshness_result.score
            * FINAL_SCORE_WEIGHTS["freshness"]
        )

        if TOTAL_WEIGHT <= 0:
            raise ValueError(
                "TOTAL_WEIGHT must be greater than zero."
            )

        overall_score = round(
            weighted_score / TOTAL_WEIGHT,
            2,
        )

        shortlist_bucket = self.bucket.get_bucket(
            overall_score,
        )

        apply_priority = int(
            round(overall_score),
        )

        if overall_score >= 90:
            recommendation = "Apply Immediately"

        elif overall_score >= 80:
            recommendation = "High Priority"

        elif overall_score >= 70:
            recommendation = "Good Match"

        elif overall_score >= 60:
            recommendation = "Stretch Role"

        else:
            recommendation = "Skip"

        explanation = (
            f"Overall Score: {overall_score:.2f}. "
            f"Bucket: {shortlist_bucket}. "
            f"Recommendation: {recommendation}."
        )

        return FinalScoreResult(
            overall_score=overall_score,
            shortlist_bucket=shortlist_bucket,
            apply_priority=apply_priority,
            recommendation=recommendation,
            explanation=explanation,
        )