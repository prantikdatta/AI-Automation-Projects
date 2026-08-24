from __future__ import annotations

from job_search_automation.orchestrators.daily_run import DailyRun


def main() -> None:
    print("=" * 80)
    print("JOB SEARCH AUTOMATION - PRODUCTION RUN")
    print("=" * 80)

    runner = DailyRun()

    result = runner.run()

    print("=" * 80)
    print("PRODUCTION RUN COMPLETED")
    print("=" * 80)
    print(f"Collected jobs : {result.collected}")
    print(f"Enriched jobs  : {result.enriched}")
    print(f"Evaluated jobs : {result.evaluated}")
    print(f"Selected jobs  : {result.selected}")
    print(f"Sheets rows    : {result.sheets_rows}")
    print("=" * 80)


if __name__ == "__main__":
    main()