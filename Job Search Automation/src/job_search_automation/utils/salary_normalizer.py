from __future__ import annotations

import re


class SalaryNormalizer:
    """
    Provider-independent salary normalization.

    Every provider benefits automatically.

    Returns

        salary_min
        salary_max
        currency
        confidence
    """

    DEFAULT_CURRENCY = "INR"

    @classmethod
    def normalize(

        cls,

        salary_min: float | int | None,

        salary_max: float | int | None,

        currency: str | None,

        description: str | None,

    ) -> tuple[
        float | None,
        float | None,
        str | None,
        float | None,
    ]:

        # --------------------------------------------------
        # Provider already supplied salary
        # --------------------------------------------------

        if salary_min or salary_max:

            confidence = 1.0

            return (

                float(salary_min)
                if salary_min
                else None,

                float(salary_max)
                if salary_max
                else None,

                currency or cls.DEFAULT_CURRENCY,

                confidence,

            )

        # --------------------------------------------------
        # Parse description
        # --------------------------------------------------

        if not description:

            return (

                None,
                None,
                None,
                None,

            )

        text = description.lower()

        pattern = (
            r"(\d+(?:\.\d+)?)"
            r"\s*"
            r"(lpa|lakhs?|lac|cr|crore)"
        )

        matches = re.findall(
            pattern,
            text,
        )

        if not matches:

            return (

                None,
                None,
                None,
                None,

            )

        values = []

        for number, unit in matches:

            value = float(number)

            if unit.startswith("cr"):

                value *= 100

            values.append(value)

        values.sort()

        if len(values) == 1:

            return (

                values[0],
                values[0],
                "INR",
                0.60,

            )

        return (

            values[0],
            values[-1],
            "INR",
            0.75,

        )