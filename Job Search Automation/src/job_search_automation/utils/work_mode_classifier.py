from __future__ import annotations


class WorkModeClassifier:
    """
    Determines a normalized work mode.

    Returns

    Remote
    Hybrid
    Onsite
    Unknown
    """

    REMOTE_KEYWORDS = (
        "remote",
        "work from home",
        "wfh",
        "distributed",
    )

    HYBRID_KEYWORDS = (
        "hybrid",
    )

    @classmethod
    def classify(
        cls,
        location: str | None,
        description: str | None,
        remote_flag: bool | None,
    ) -> str:

        if remote_flag:
            return "Remote"

        text = f"{location or ''} {description or ''}".lower()

        for keyword in cls.REMOTE_KEYWORDS:

            if keyword in text:
                return "Remote"

        for keyword in cls.HYBRID_KEYWORDS:

            if keyword in text:
                return "Hybrid"

        if location:
            return "Onsite"

        return "Unknown"