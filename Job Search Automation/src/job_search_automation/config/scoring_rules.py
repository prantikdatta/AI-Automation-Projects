"""
Scoring Rules

Purpose
-------
Central configuration for all deterministic scoring
performed by the intelligence layer.

This file MUST NOT contain business logic.

Only weights, thresholds and score mappings belong here.
"""

# ==========================================================
# FINAL SCORE WEIGHTS
# ==========================================================
#
# Total = 100
#

FINAL_SCORE_WEIGHTS = {

    "skill_match": 30,

    "experience_match": 20,

    "career_progression": 15,

    "job_freshness": 15,

    "location_match": 8,

    "company_score": 7,

    "work_mode": 3,

    "industry_match": 2,

}

# ==========================================================
# SHORTLIST THRESHOLDS
# ==========================================================

SHORTLIST_THRESHOLDS = {

    "must_apply": 90,

    "high_priority": 80,

    "good_fit": 70,

    "consider": 60,

    "reject": 0,

}

# ==========================================================
# EXPERIENCE SCORING
# ==========================================================

EXPERIENCE_SCORE = {

    "gap_greater_equal_2": 100,

    "gap_greater_equal_0": 95,

    "gap_greater_equal_minus_1": 80,

    "gap_greater_equal_minus_2": 60,

    "gap_less_minus_2": 30,

    "experience_not_found": 70,

}

# ==========================================================
# JOB FRESHNESS
# ==========================================================

FRESHNESS_SCORE = {

    "within_24_hours": 100,

    "within_72_hours": 90,

    "within_7_days": 70,

    "older_than_7_days": 0,

}

# ==========================================================
# LOCATION
# ==========================================================

LOCATION_SCORE = {

    # Navi Mumbai / Mumbai / Thane
    "primary": 100,

    # Fully Remote
    "remote": 98,

    # International Opportunity
    "international": 95,

    # Bangalore / Pune
    "secondary": 92,

    # Delhi NCR / Gurugram / Gurgaon
    "tertiary": 85,

    # Same preferred state
    "state": 75,

    # Hybrid
    "hybrid": 70,

    # Everything else
    "other": 30,

}

# ==========================================================
# WORK MODE
# ==========================================================

WORK_MODE_SCORE = {

    "remote": 100,

    "hybrid": 90,

    "onsite": 80,

    "unknown": 60,

}

# ==========================================================
# CAREER PROGRESSION
# ==========================================================

CAREER_PROGRESSION_SCORE = {

    "ideal_growth": 100,

    "promotion": 98,

    "lateral": 85,

    "slight_downgrade": 50,

    "major_downgrade": 0,

    "overqualified": 70,

}

# ==========================================================
# COMPANY
# ==========================================================

COMPANY_SCORE = {

    "faang": 100,

    "mbb": 100,

    "tier1_product": 95,

    "tier1_consulting": 95,

    "fortune500": 92,

    "fintech": 90,

    "global_mnc": 88,

    "tier2": 82,

    "startup": 75,

    "unknown": 65,

}

# ==========================================================
# INDUSTRY
# ==========================================================

INDUSTRY_SCORE = {

    "preferred": 100,

    "related": 80,

    "neutral": 60,

    "unknown": 50,

}

# ==========================================================
# SKILL MATCH
# ==========================================================

SKILL_MATCH = {

    "excellent": 90,

    "strong": 75,

    "average": 60,

    "weak": 40,

    "poor": 20,

}

# ==========================================================
# GEMINI
# ==========================================================

GEMINI_SCORE = {

    "minimum_confidence": 0.75,

    "temperature": 0.20,

}

# ==========================================================
# PIPELINE LIMITS
# ==========================================================

PIPELINE_LIMITS = {

    "max_jobs_after_search": 750,

    "max_jobs_after_deduplication": 250,

    "max_jobs_after_scoring": 100,

    "max_jobs_for_resume_tailoring": 25,

    "max_jobs_to_google_sheet": 100,

}

# ==========================================================
# SEARCH LIMITS
# ==========================================================

SEARCH_LIMITS = {

    "max_days_old": 7,

    "preferred_days": 3,

    "minimum_results_per_role": 50,

    "minimum_final_jobs": 50,

}

# ==========================================================
# DUPLICATE DETECTION
# ==========================================================

DUPLICATE_RULES = {

    "company_weight": 0.35,

    "title_weight": 0.45,

    "location_weight": 0.20,

    "similarity_threshold": 0.90,

}

# ==========================================================
# DEFAULT VALUES
# ==========================================================

DEFAULTS = {

    "unknown_company_score": 65,

    "unknown_location_score": 50,

    "unknown_experience_score": 70,

    "unknown_skill_score": 50,

}