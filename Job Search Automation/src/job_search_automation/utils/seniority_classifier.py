from __future__ import annotations


class SeniorityClassifier:
    """
    Provider-independent seniority classifier.
    """

    LEVELS = {

        "Intern": (
            "intern",
            "internship",
        ),

        "Entry": (
            "entry",
            "junior",
            "associate",
            "graduate",
            "fresher",
        ),

        "Mid": (
            "analyst",
            "engineer",
            "developer",
            "consultant",
            "specialist",
        ),

        "Senior": (
            "senior",
            "lead",
            "principal",
            "staff",
        ),

        "Manager": (
            "manager",
            "head",
            "director",
            "vp",
            "vice president",
        ),

    }

    @classmethod
    def classify(
        cls,
        title: str | None,
        description: str | None,
    ) -> str | None:

        text = f"{title or ''} {description or ''}".lower()

        for level, keywords in cls.LEVELS.items():

            for keyword in keywords:

                if keyword in text:
                    return level

        return None