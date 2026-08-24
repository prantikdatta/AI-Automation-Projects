"""
Utility functions for converting numerical scores
into human-readable recommendation buckets.
"""


class ScoreBucket:
    """
    Converts a numerical score into a qualitative bucket.
    """

    def get_bucket(
        self,
        score: float,
    ) -> str:

        if score >= 90:

            return "Excellent"

        if score >= 80:

            return "Very Good"

        if score >= 70:

            return "Good"

        if score >= 60:

            return "Average"

        return "Poor"