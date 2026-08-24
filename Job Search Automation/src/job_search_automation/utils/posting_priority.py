from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone


class PostingPriority:
    """
    Determines application priority solely from posting age.

    Priority Scale
    --------------
    100 -> within 24 hours

    80 -> within 3 days

    60 -> within 7 days

    40 -> within 14 days

    0 -> older than 14 days
    """

    PRIORITY_24_HOURS = 100

    PRIORITY_3_DAYS = 80

    PRIORITY_7_DAYS = 60

    PRIORITY_14_DAYS = 40

    PRIORITY_EXPIRED = 0

    @classmethod
    def classify(
        cls,
        posted_at: datetime | None,
    ) -> int:

        if posted_at is None:

            return cls.PRIORITY_7_DAYS

        if posted_at.tzinfo is None:

            posted_at = posted_at.replace(
                tzinfo=timezone.utc,
            )

        now = datetime.now(
            timezone.utc,
        )

        age = now - posted_at

        if age <= timedelta(hours=24):

            return cls.PRIORITY_24_HOURS

        if age <= timedelta(days=3):

            return cls.PRIORITY_3_DAYS

        if age <= timedelta(days=7):

            return cls.PRIORITY_7_DAYS

        if age <= timedelta(days=14):

            return cls.PRIORITY_14_DAYS

        return cls.PRIORITY_EXPIRED