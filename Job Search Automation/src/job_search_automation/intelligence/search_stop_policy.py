from __future__ import annotations


class SearchStopPolicy:
    """
    Determines whether searching should continue.

    Stops searching once the desired
    number of quality jobs has been collected.
    """

    def __init__(
        self,
        target_jobs: int,
    ):

        self.target_jobs = target_jobs

    def should_stop(
        self,
        collected_jobs: int,
    ) -> bool:

        return collected_jobs >= self.target_jobs