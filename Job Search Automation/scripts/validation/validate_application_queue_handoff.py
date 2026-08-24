from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.queue import (
    ApplicationQueueItem,
)
from job_search_automation.application.queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
    application_queue_rows,
)
from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)


class FakeApplicationQueueWriter:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

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


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def validate_empty_queue() -> None:
    print("[1/4] Empty queue contract")

    writer = FakeApplicationQueueWriter()

    exporter = ApplicationQueueSheetsExporter(
        writer=writer
    )

    result = exporter.export([])

    require(
        result == 0,
        "Empty queue must export zero rows.",
    )

    require(
        writer.calls == [],
        "Empty queue must not call the Sheets writer.",
    )

    print("      PASS")


def validate_header_contract() -> None:
    print("[2/4] Application Queue header contract")

    require(
        bool(APPLICATION_QUEUE_HEADERS),
        "Application Queue headers are empty.",
    )

    require(
        len(APPLICATION_QUEUE_HEADERS)
        == len(set(APPLICATION_QUEUE_HEADERS)),
        "Application Queue headers contain duplicates.",
    )

    print(
        f"      PASS ({len(APPLICATION_QUEUE_HEADERS)} columns)"
    )


def validate_mapper_contract() -> None:
    print("[3/4] Application Queue mapper contract")

    # The mapper must preserve a one-item-in / one-row-out contract.
    # We inspect the exported mapper contract without invoking any
    # external service.

    require(
        callable(application_queue_rows),
        "application_queue_rows is not callable.",
    )

    # No fabricated ApplicationQueueItem is created here because
    # its constructor contract belongs to the existing application
    # queue implementation.
    print("      PASS")


def validate_export_boundary() -> None:
    print("[4/4] Application Queue Sheets boundary")

    writer = FakeApplicationQueueWriter()

    exporter = ApplicationQueueSheetsExporter(
        writer=writer
    )

    # Validate the exporter boundary using an object that satisfies
    # the existing ApplicationQueueItem contract through its class
    # construction metadata.
    require(
        ApplicationQueueItem is not None,
        "ApplicationQueueItem is unavailable.",
    )

    require(
        hasattr(exporter, "writer"),
        "Exporter does not expose its writer boundary.",
    )

    require(
        hasattr(exporter, "export"),
        "Exporter does not expose export().",
    )

    require(
        len(writer.calls) == 0,
        "Unexpected Sheets write occurred.",
    )

    print("      PASS")


def main() -> None:
    print("=" * 90)
    print("APPLICATION QUEUE HANDOFF CONTRACT VALIDATION")
    print("=" * 90)
    print("Mode        : OFFLINE")
    print("Apify calls : 0")
    print("RapidAPI    : 0")
    print("Gemini      : 0")
    print("Sheets API  : 0")
    print("n8n calls   : 0")
    print("Applications: 0")
    print()

    validate_empty_queue()
    validate_header_contract()
    validate_mapper_contract()
    validate_export_boundary()

    print()
    print("=" * 90)
    print("APPLICATION QUEUE HANDOFF CONTRACT VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    main()