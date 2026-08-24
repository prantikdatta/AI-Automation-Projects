"""
Central Search Strategy

This file is the ONLY place where the application knows:

• What roles to search
• Where to search
• Which providers are enabled
• Freshness rules
• Search limits
• Category priorities

Nothing else in the application should hardcode these values.
"""

# ==========================================================
# ROLE STRATEGY
# ==========================================================

SEARCH_ROLES = {

    "Analytics": {
        "weight": 1.00,
        "career_stage": "Core",
        "roles": [
            "Data Analyst",
            "Senior Data Analyst",
            "Analytics Engineer",
            "Reporting Analyst",
            "Data Analytics Consultant",
            "Decision Scientist",
            "Insights Analyst",
        ],
    },

    "Business Intelligence": {
        "weight": 0.98,
        "career_stage": "Core",
        "roles": [
            "Business Intelligence Analyst",
            "Business Intelligence Developer",
            "BI Analyst",
            "BI Developer",
            "Power BI Developer",
            "Power BI Analyst",            
        ],
    },

    "Business Analysis": {
        "weight": 0.97,
        "career_stage": "Core",
        "roles": [
            "Business Analyst",
            "Senior Business Analyst",
            "Functional Analyst",
            "Business Systems Analyst",
        ],
    },

    "Consulting": {
        "weight": 0.96,
        "career_stage": "Growth",
        "roles": [
            "Analytics Consultant",
            "Technology Consultant",
            "Strategy Consultant",
            "Business Consultant",
            "Digital Transformation Consultant",
            "Management Consultant",
        ],
    },

    "Product Analytics": {
        "weight": 0.95,
        "career_stage": "Growth",
        "roles": [
            "Product Analyst",
            "Senior Product Analyst",
            "Product Analytics",
            "Product Analytics Manager",
            "Growth Analyst",
            "Growth Analytics",
        ],
    },

    "Risk & Banking": {
        "weight": 0.94,
        "career_stage": "Growth",
        "roles": [
            "Risk Analyst",
            "Senior Risk Analyst",
            "Credit Risk Analyst",
            "Fraud Analyst",
            "Risk Consultant",
            "Senior Risk Consultant",
            "Credit Strategy Analyst",
        ],
    },

    "Program & PMO": {
        "weight": 0.93,
        "career_stage": "Growth",
        "roles": [
            "PMO Analyst",
            "Program Analyst",
            "Project Analyst",
            "Program Manager",
            "Technical Program Manager",
            "Project Manager",
        ],
    },

    "Leadership": {
        "weight": 0.90,
        "career_stage": "Promotion",
        "roles": [
            "Analytics Manager",
            "Business Intelligence Manager",
            "Data Manager",
            "Manager Analytics",
            "Manager Business Intelligence",
            "Senior Manager Analytics",
            "Lead Data Analyst",
            "Associate Director Analytics",
            "AVP Analytics",
            "AVP Business Intelligence",
            "Associate Manager Analytics",
            "Lead Business Analyst",
            "Lead Analytics Consultant",
        ],
    },
}

# ==========================================================
# LOCATIONS
# ==========================================================

SEARCH_LOCATIONS = [

    "Mumbai",

    "Navi Mumbai",

    "Pune",

    "Bangalore",

    "Hyderabad",

    "Gurugram",

    "Remote India"

]

# ==========================================================
# FRESHNESS STRATEGY
# ==========================================================

SEARCH_WINDOWS = [

    {
        "days": 1,
        "priority": 100,
        "label": "Last 24 Hours",
        "provider_value": "today",
    },

    {
        "days": 3,
        "priority": 80,
        "label": "24-72 Hours",
        "provider_value": "3days",
    },

    {
        "days": 7,
        "priority": 60,
        "label": "3-7 Days",
        "provider_value": "week",
    },

]

# ==========================================================
# SEARCH LIMITS
# ==========================================================

SEARCH_LIMITS = {

    # Pages fetched from each provider
    "pages_per_provider": 5,

    # Approximate jobs returned per page
    "jobs_per_page": 10,

    # Stop searching once this many jobs remain after deduplication
    "target_jobs": 100,

    # If fewer than this are found, broaden search
    "minimum_jobs": 50,

    # Maximum jobs allowed before AI processing
    "max_jobs_before_scoring": 500,

}

# ==========================================================
# DEFAULT SEARCH SETTINGS
# ==========================================================

DEFAULT_COUNTRY = "in"

DEFAULT_REMOTE_ONLY = False


# ==========================================================
# PROVIDERS
# ==========================================================

ENABLED_PROVIDERS = [

    "rapidapi",

    #"apify",

    #"adzuna",

]