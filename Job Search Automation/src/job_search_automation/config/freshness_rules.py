"""
Freshness Rules

Defines how job age influences ranking.

Business logic belongs in FreshnessScorer.
"""

# ==========================================================
# MAXIMUM ACCEPTABLE AGE
# ==========================================================

MAX_JOB_AGE_DAYS = 7

# ==========================================================
# FRESHNESS WINDOWS
# ==========================================================

FRESHNESS_WINDOWS = {

    "today": {

        "min_hours": 0,
        "max_hours": 24,

    },

    "recent": {

        "min_hours": 24,
        "max_hours": 72,

    },

    "week": {

        "min_hours": 72,
        "max_hours": 168,

    },

}

# ==========================================================
# FRESHNESS SCORES
# ==========================================================

FRESHNESS_SCORE = {

    "today": 100,

    "recent": 90,

    "week": 75,

    "expired": 0,

}