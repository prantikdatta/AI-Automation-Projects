"""
Final Score Weights

These weights determine how much each scorer contributes
to the overall Resume Match Score.

All weights must sum to 100.
"""

FINAL_SCORE_WEIGHTS = {

    # Resume Skill Match
    "skills": 30,

    # Years of Experience
    "experience": 20,

    # Career Progression
    "career": 15,

    # Preferred Location
    "location": 10,

    # Employer Quality
    "company": 10,

    # Job Freshness
    "freshness": 15,

}

TOTAL_WEIGHT = sum(FINAL_SCORE_WEIGHTS.values())