from __future__ import annotations

import re


# ============================================================
# EXCLUSION RULES
# ============================================================

INTERNSHIP_WORDS = [
    "intern",
    "internship",
    "trainee",
    "apprentice",
    "campus",
    "graduate program",
    "fresh graduate",
    "student",
    "unpaid",
    "stipend",
]


FOREIGN_WORDS = [
    "usa",
    "united states",
    "canada",
    "uk",
    "united kingdom",
    "europe",
    "australia",
    "citizens only",
    "visa sponsorship",
]


SENIOR_WORDS = [
    "director",
    "principal",
    "head",
    "chief",
    "vp",
]


MAX_EXPERIENCE = 10


# ============================================================
# HELPERS
# ============================================================

def contains_any(
    text: str,
    words: list[str],
) -> bool:

    text = (text or "").lower()

    return any(
        word.lower() in text
        for word in words
    )


def extract_experience(
    description: str,
) -> int | None:

    patterns = [
        r"(\d+)\+?\s*years",
        r"experience[: ]+(\d+)",
    ]

    text = (description or "").lower()

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


# ============================================================
# MAIN PREFILTER
# ============================================================

def should_reject(job) -> bool:
    """
    Performs deterministic pre-screening before enrichment.

    Returns:
        True  -> reject the job
        False -> keep the job
    """

    title = (
        getattr(job, "title", "")
        or ""
    ).strip()

    description = (
        getattr(job, "description", "")
        or ""
    ).strip()

    company = (
        getattr(job, "company", "")
        or ""
    ).strip()

    location = (
        getattr(job, "location", "")
        or ""
    ).strip()

    title_lower = title.lower()

    description_lower = description.lower()

    combined = (
        f"{title_lower} "
        f"{description_lower}"
    )

    # ---------------------------------------------------------
    # Reject internships / entry programs
    # ---------------------------------------------------------

    if contains_any(
        combined,
        INTERNSHIP_WORDS,
    ):
        return True

    # ---------------------------------------------------------
    # Reject explicitly foreign opportunities
    # ---------------------------------------------------------

    if contains_any(
        combined,
        FOREIGN_WORDS,
    ):
        return True

    # ---------------------------------------------------------
    # Reject senior leadership roles
    # ---------------------------------------------------------

    if contains_any(
        title_lower,
        SENIOR_WORDS,
    ):
        return True

    # ---------------------------------------------------------
    # Reject roles requiring > MAX_EXPERIENCE years
    # ---------------------------------------------------------

    experience = extract_experience(
        description
    )

    if (
        experience is not None
        and experience > MAX_EXPERIENCE
    ):
        return True

    # ---------------------------------------------------------
    # Reject structurally invalid jobs
    #
    # This prevents malformed ATS/API records from reaching
    # enrichment, scoring, resume matching and Sheets export.
    # ---------------------------------------------------------

    if not title:
        return True

    if not company:
        return True

    if not location:
        return True

    if not getattr(
        job,
        "job_url",
        None,
    ):
        return True

    return False