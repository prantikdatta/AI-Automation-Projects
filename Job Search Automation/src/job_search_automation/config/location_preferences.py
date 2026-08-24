"""
Candidate location preferences.

This module is consumed by the LocationMatcher.

Priority

1. Preferred Cities
2. Preferred States
3. Remote
4. Hybrid
5. Others
"""

# ==========================================================
# PRIMARY CITIES
# ==========================================================

PREFERRED_CITIES = [

    "Navi Mumbai",

    "Mumbai",

    "Thane",

    "Bengaluru",

    "Bangalore",

    "Pune",

    "Hyderabad",

]

# ==========================================================
# PREFERRED STATES
# ==========================================================

PREFERRED_STATES = [

    "Maharashtra",

    "Karnataka",

    "Telangana",

    "Delhi",

    "Haryana",

]

# ==========================================================
# REMOTE / HYBRID
# ==========================================================

ALLOW_REMOTE = True

ALLOW_HYBRID = True

ALLOW_RELOCATION = True

ALLOW_INTERNATIONAL = True

# ==========================================================
# OPTIONAL LOCATION GROUPS
# (Used by future ranking modules)
# ==========================================================

PRIMARY_LOCATIONS = [

    "Navi Mumbai",

    "Mumbai",

    "Thane",

]

SECONDARY_LOCATIONS = [

    "Bengaluru",

    "Bangalore",

    "Pune",

    "Hyderabad",

]

TERTIARY_LOCATIONS = [

    "Delhi",

    "New Delhi",

    "Noida",

    "Gurugram",

    "Gurgaon",

]

# ==========================================================
# LOCATION PRIORITY
# ==========================================================

LOCATION_PRIORITY = {

    "preferred_city": 1,

    "preferred_state": 2,

    "remote": 3,

    "hybrid": 4,

    "other": 5,

}