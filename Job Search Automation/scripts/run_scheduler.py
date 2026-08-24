from __future__ import annotations

import logging
import sys

from job_search_automation.orchestrators.daily_run import main


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    sys.exit(main())