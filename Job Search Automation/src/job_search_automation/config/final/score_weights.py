"""
Deterministic final-score weights.

All weights are expressed as relative percentages and
must sum to 100.
"""

FINAL_SCORE_WEIGHTS: dict[str, float] = {
    "skills": 30.0,
    "experience": 20.0,
    "career": 15.0,
    "location": 10.0,
    "company": 10.0,
    "freshness": 15.0,
}

TOTAL_WEIGHT = sum(
    FINAL_SCORE_WEIGHTS.values()
)


if TOTAL_WEIGHT != 100.0:
    raise ValueError(
        "FINAL_SCORE_WEIGHTS must sum to exactly 100."
    )