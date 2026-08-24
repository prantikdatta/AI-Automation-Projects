"""
Company Preferences

This module contains only configuration.

It defines company priorities, tiers and industry
preferences.

No business logic belongs here.
"""

# ==========================================================
# DREAM EMPLOYERS (TIER 1)
# ==========================================================

TIER_1_COMPANIES = [

    # FAANG / Big Tech
    "Google",
    "Microsoft",
    "Amazon",
    "Meta",
    "Apple",
    "Netflix",

    # Data / AI
    "OpenAI",
    "NVIDIA",
    "Databricks",
    "Snowflake",
    "Palantir",

    # Consulting
    "McKinsey & Company",
    "Boston Consulting Group",
    "Bain & Company",

]

# ==========================================================
# PREMIUM CONSULTING
# ==========================================================

CONSULTING_COMPANIES = [

    "Accenture",
    "Deloitte",
    "PwC",
    "EY",
    "KPMG",
    "Capgemini",
    "Cognizant",
    "Infosys Consulting",
    "TCS",
    "Wipro",

]

# ==========================================================
# PRODUCT COMPANIES
# ==========================================================

PRODUCT_COMPANIES = [

    "Atlassian",
    "Salesforce",
    "Adobe",
    "Oracle",
    "SAP",
    "ServiceNow",
    "Cisco",
    "VMware",
    "Intuit",

]

# ==========================================================
# FINTECH
# ==========================================================

FINTECH_COMPANIES = [

    "Razorpay",
    "PhonePe",
    "Paytm",
    "Pine Labs",
    "CRED",
    "Groww",
    "Zerodha",
    "Jupiter",
    "Fi Money",
    "Navi",

]

# ==========================================================
# BANKS & FINANCIAL SERVICES
# ==========================================================

BANKS = [

    "JPMorgan Chase",
    "Morgan Stanley",
    "Goldman Sachs",
    "Barclays",
    "HSBC",
    "Citi",
    "Deutsche Bank",
    "Standard Chartered",
    "American Express",
    "Mastercard",
    "Visa",

]

# ==========================================================
# GLOBAL CAPABILITY CENTERS
# ==========================================================

GCC_COMPANIES = [

    "FedEx",
    "Target",
    "Walmart Global Tech",
    "Lowe's",
    "Shell",
    "Boeing",
    "Honeywell",
    "Siemens",
    "PepsiCo",
    "Unilever",

]

# ==========================================================
# UNICORNS
# ==========================================================

UNICORNS = [

    "Flipkart",
    "Swiggy",
    "Meesho",
    "Dream11",
    "Myntra",
    "Freshworks",
    "Postman",

]

# ==========================================================
# INDUSTRY PRIORITY
# ==========================================================

INDUSTRY_PRIORITY = {

    "Consulting": 100,

    "Artificial Intelligence": 98,

    "Product": 96,

    "FinTech": 95,

    "Banking": 94,

    "Payments": 94,

    "Analytics": 93,

    "Cloud": 92,

    "Software": 90,

    "Logistics": 88,

    "Healthcare": 85,

    "Retail": 84,

    "Manufacturing": 82,

    "Telecom": 80,

}

# ==========================================================
# COMPANY TIER SCORE
# ==========================================================

COMPANY_TIER_SCORE = {

    "Tier1": 100,

    "Consulting": 97,

    "Product": 96,

    "FinTech": 95,

    "Bank": 94,

    "GCC": 92,

    "Unicorn": 91,

    "Other": 75,

}

# ==========================================================
# NORMALIZATION
# ==========================================================

COMPANY_ALIASES = {

    "JPMC": "JPMorgan Chase",

    "JP Morgan": "JPMorgan Chase",

    "BCG": "Boston Consulting Group",

    "McKinsey": "McKinsey & Company",

    "Bain": "Bain & Company",

    "GS": "Goldman Sachs",

    "MS": "Morgan Stanley",

    "Amex": "American Express",

    "SCB": "Standard Chartered",

}