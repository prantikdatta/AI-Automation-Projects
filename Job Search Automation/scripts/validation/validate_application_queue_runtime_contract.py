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
    application_queue_rows,
)
from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class FakeSheetsService:
    def __init__(self) -> None:
        self.calls = []

    def append_application_queue(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> None:
        self.calls.append(
            {
                "headers": headers,
                "rows": rows,
            }
        )


def validate_writer_contract() -> None:
    print("[1/3] Google Sheets writer contract")

    service = object.__new__(GoogleSheetsService)

    require(
        hasattr(service, "append_application_queue"),
        "GoogleSheetsService missing append_application_queue().",
    )

    require(
        callable(service.append_application_queue),
        "append_application_queue is not callable.",
    )

    print("      PASS")


def validate_exporter_boundary() -> None:
    print("[2/3] Exporter boundary")

    writer = FakeSheetsService()

    exporter = ApplicationQueueSheetsExporter(
        writer=writer
    )

    require(
        exporter.writer is writer,
        "Exporter writer dependency was not preserved.",
    )

    require(
        callable(exporter.export),
        "Exporter export() missing.",
    )

    require(
        callable(application_queue_rows),
        "Application Queue mapper missing.",
    )

    print("      PASS")


def validate_schema() -> None:
    print("[3/3] Application Queue schema")

    require(
        len(APPLICATION_QUEUE_HEADERS) == 14,
        (
            "Unexpected Application Queue schema width: "
            f"{len(APPLICATION_QUEUE_HEADERS)}; expected 14."
        ),
    )

    require(
        len(APPLICATION_QUEUE_HEADERS)
        == len(set(APPLICATION_QUEUE_HEADERS)),
        "Application Queue schema contains duplicate headers.",
    )

    print("      PASS")


def main() -> None:
    print("=" * 90)
    print("APPLICATION QUEUE RUNTIME CONTRACT VALIDATION")
    print("=" * 90)
    print("Mode        : OFFLINE")
    print("Apify calls : 0")
    print("RapidAPI    : 0")
    print("Gemini      : 0")
    print("Sheets API  : 0")
    print("n8n calls   : 0")
    print("Applications: 0")
    print()

    validate_writer_contract()
    validate_exporter_boundary()
    validate_schema()

    print()
    print("=" * 90)
    print("APPLICATION QUEUE RUNTIME CONTRACT VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    main()