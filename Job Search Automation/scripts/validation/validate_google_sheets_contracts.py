from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.models.job import Job
from job_search_automation.pipeline.unique_jobs_export_stage import (
    UniqueJobsExportStage,
)
from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)
from job_search_automation.application.queue_sheets import (
    ApplicationQueueSheetsExporter,
)
from job_search_automation.application.queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
)


class FakeWorksheet:
    def __init__(
        self,
        values: list[list[str]] | None = None,
    ) -> None:
        self.values = values or []
        self.title = "Validation"

        self.updated: list[dict[str, Any]] = []
        self.appended: list[list[str]] = []
        self.append_rows_calls: list[list[list[str]]] = []

    def get_all_values(self) -> list[list[str]]:
        return self.values

    def update(
        self,
        *,
        range_name: str,
        values: list[list[str]],
        value_input_option: str,
    ) -> None:
        self.updated.append(
            {
                "range_name": range_name,
                "values": values,
                "value_input_option": value_input_option,
            }
        )

    def append_row(
        self,
        values: list[str],
        value_input_option: str,
    ) -> None:
        self.appended.append(values)

    def append_rows(
        self,
        values: list[list[str]],
        value_input_option: str,
    ) -> None:
        self.append_rows_calls.append(values)

    def clear(self) -> None:
        self.values = []


class FakeSheetsWriter:
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


class FakeUniqueJobsSheetsService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def append_unique_jobs(
        self,
        headers: list[str],
        rows: list[list[Any]],
    ) -> int:
        self.calls.append(
            {
                "headers": headers,
                "rows": rows,
            }
        )

        return len(rows)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def build_test_job() -> Job:
    return Job(
        title="Data Analyst",
        company="Validation Company",
        location="Mumbai",
        job_url="https://example.com/job/validation",
        source="validation",
        provider="validation",
        searched_role="Data Analyst",
        posted_at="2026-08-19",
    )


def validate_google_sheets_helpers() -> None:
    print("[1/4] GoogleSheetsService helper contracts")

    service = object.__new__(
        GoogleSheetsService
    )

    require(
        service._column_letter(1) == "A",
        "_column_letter(1) failed.",
    )

    require(
        service._column_letter(26) == "Z",
        "_column_letter(26) failed.",
    )

    require(
        service._column_letter(27) == "AA",
        "_column_letter(27) failed.",
    )

    require(
        service._range_for_rows(
            start_row=2,
            row_count=4,
            column_count=8,
        )
        == "A2:H5",
        "_range_for_rows produced incorrect range.",
    )

    require(
        service._normalise_row(
            ["abc", None, 123]
        )
        == ["abc", "", "123"],
        "_normalise_row failed.",
    )

    print("      PASS")


def validate_header_contract() -> None:
    print("[2/4] Header initialization / validation")

    service = object.__new__(
        GoogleSheetsService
    )

    worksheet = FakeWorksheet()

    headers = [
        "title",
        "company",
        "location",
    ]

    service._ensure_headers(
        worksheet,
        headers,
        "Validation",
    )

    require(
        len(worksheet.updated) == 1,
        "Empty worksheet did not receive headers.",
    )

    require(
        worksheet.updated[0]["range_name"] == "A1:C1",
        "Header range is incorrect.",
    )

    require(
        worksheet.updated[0]["values"] == [headers],
        "Header values are incorrect.",
    )

    worksheet.values = [headers]

    service._ensure_headers(
        worksheet,
        headers,
        "Validation",
    )

    require(
        len(worksheet.updated) == 1,
        "Matching headers were unexpectedly rewritten.",
    )

    failed = False

    try:
        service._ensure_headers(
            worksheet,
            ["wrong", "headers", "here"],
            "Validation",
        )
    except ValueError:
        failed = True

    require(
        failed,
        "Header mismatch did not fail loudly.",
    )

    print("      PASS")


def validate_application_queue_exporter() -> None:
    print("[3/4] Application Queue exporter contract")

    writer = FakeSheetsWriter()

    exporter = ApplicationQueueSheetsExporter(
        writer=writer
    )

    # Queue mapper owns the exact ApplicationQueueItem shape.
    # We validate the writer boundary with an empty export because
    # the exporter must not issue a Sheets call when there is no queue.
    result = exporter.export([])

    require(
        result == 0,
        "Empty Application Queue export must return zero.",
    )

    require(
        writer.calls == [],
        "Empty Application Queue export issued a Sheets write.",
    )

    require(
        len(APPLICATION_QUEUE_HEADERS) > 0,
        "Application Queue headers are empty.",
    )

    print("      PASS")


def validate_unique_jobs_export() -> None:
    print("[4/4] Unique Jobs export contract")

    sheets_service = FakeUniqueJobsSheetsService()

    stage = UniqueJobsExportStage(
        sheets_service=sheets_service
    )

    job = build_test_job()

    rows = stage.build_rows([job])

    require(
        len(rows) == 1,
        "Unique Jobs mapper produced incorrect row count.",
    )

    require(
        len(rows[0]) == len(stage.HEADERS),
        (
            "Unique Jobs row width mismatch: "
            f"row={len(rows[0])}, "
            f"headers={len(stage.HEADERS)}."
        ),
    )

    exported = stage.export([job])

    require(
        exported == 1,
        "Unique Jobs export returned incorrect count.",
    )

    require(
        len(sheets_service.calls) == 1,
        "Unique Jobs Sheets boundary was not called exactly once.",
    )

    call = sheets_service.calls[0]

    require(
        call["headers"] == stage.HEADERS,
        "Unique Jobs headers changed unexpectedly.",
    )

    require(
        len(call["rows"]) == 1,
        "Unique Jobs export row count mismatch.",
    )

    print("      PASS")


def main() -> None:
    print("=" * 90)
    print("GOOGLE SHEETS CONTRACT VALIDATION")
    print("=" * 90)
    print("Mode        : OFFLINE")
    print("Apify calls : 0")
    print("RapidAPI    : 0")
    print("Gemini      : 0")
    print("Sheets API  : 0")
    print()

    validate_google_sheets_helpers()
    validate_header_contract()
    validate_application_queue_exporter()
    validate_unique_jobs_export()

    print()
    print("=" * 90)
    print("GOOGLE SHEETS CONTRACT VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    main()