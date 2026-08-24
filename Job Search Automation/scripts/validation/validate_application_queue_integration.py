from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)
from job_search_automation.application.queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
)
from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)


class FakeWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], list[list[str]]]] = []

    def append_application_queue(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> None:
        self.calls.append((headers, rows))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_google_sheets_boundary() -> None:
    print("[1/3] GoogleSheetsService → Application Queue boundary")

    service = object.__new__(GoogleSheetsService)

    require(
        callable(
            getattr(
                service,
                "append_application_queue",
                None,
            )
        ),
        "GoogleSheetsService does not expose the required "
        "append_application_queue contract.",
    )

    require(
        callable(
            getattr(
                service,
                "clear_application_queue",
                None,
            )
        ),
        "GoogleSheetsService does not expose "
        "clear_application_queue().",
    )

    print("      PASS")


def validate_exporter() -> None:
    print("[2/3] ApplicationQueueSheetsExporter integration")

    writer = FakeWriter()

    exporter = ApplicationQueueSheetsExporter(
        writer=writer
    )

    require(
        exporter.writer is writer,
        "Exporter did not retain the supplied writer.",
    )

    result = exporter.export([])

    require(
        result == 0,
        "Empty queue must return zero.",
    )

    require(
        not writer.calls,
        "Empty queue must not write to Sheets.",
    )

    print("      PASS")


def validate_schema_boundary() -> None:
    print("[3/3] Application Queue schema boundary")

    require(
        len(APPLICATION_QUEUE_HEADERS) == 14,
        (
            "Application Queue header count changed. "
            f"Found {len(APPLICATION_QUEUE_HEADERS)}, expected 14."
        ),
    )

    require(
        all(
            isinstance(header, str)
            and header.strip()
            for header in APPLICATION_QUEUE_HEADERS
        ),
        "Application Queue contains empty or invalid headers.",
    )

    require(
        len(APPLICATION_QUEUE_HEADERS)
        == len(set(APPLICATION_QUEUE_HEADERS)),
        "Application Queue contains duplicate headers.",
    )

    print("      PASS")


def main() -> None:
    print("=" * 90)
    print("APPLICATION QUEUE INTEGRATION VALIDATION")
    print("=" * 90)
    print("Mode        : OFFLINE")
    print("Apify calls : 0")
    print("RapidAPI    : 0")
    print("Gemini      : 0")
    print("Sheets API  : 0")
    print("n8n calls   : 0")
    print("Applications: 0")
    print()

    validate_google_sheets_boundary()
    validate_exporter()
    validate_schema_boundary()

    print()
    print("=" * 90)
    print("APPLICATION QUEUE INTEGRATION VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    main()