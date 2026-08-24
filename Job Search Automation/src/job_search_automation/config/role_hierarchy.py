"""
Role Hierarchy

Defines career progression for analytics,
BI, product, consulting and PMO careers.

Lower level = Earlier career

Higher level = Better career progression
"""

ROLE_HIERARCHY = {

    # ==========================================================
    # ENTRY LEVEL
    # ==========================================================

    "intern": 1,

    "graduate trainee": 2,

    "trainee": 2,

    "associate": 3,

    "junior analyst": 4,

    "analyst": 5,

    "business analyst": 5,

    "data analyst": 5,

    "bi analyst": 5,

    "reporting analyst": 5,

    "product analyst": 5,

    "risk analyst": 5,

    # ==========================================================
    # SENIOR ANALYST
    # ==========================================================

    "senior analyst": 6,

    "senior business analyst": 6,

    "senior data analyst": 6,

    "senior bi analyst": 6,

    "analytics consultant": 6,

    # ==========================================================
    # LEAD
    # ==========================================================

    "lead analyst": 7,

    "lead consultant": 7,

    "lead data analyst": 7,

    "lead bi developer": 7,

    "technical lead": 7,

    # ==========================================================
    # MANAGEMENT
    # ==========================================================

    "assistant manager": 8,

    "manager": 9,

    "program manager": 9,

    "project manager": 9,

    "analytics manager": 9,

    "product manager": 9,

    "consultant": 9,

    "senior consultant": 10,

    # ==========================================================
    # LEADERSHIP
    # ==========================================================

    "principal consultant": 11,

    "associate vice president": 12,

    "assistant vice president": 12,

    "vice president": 13,

    "director": 14,

    "senior director": 15,

    "head": 16,

    "general manager": 16,

    "chief": 17,

    "cto": 18,

    "cio": 18,

}