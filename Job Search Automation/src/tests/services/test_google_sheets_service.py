from __future__ import annotations

from typing import List

import pytest

from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)


class FakeWorksheet:
    def __init__(
        self,
        values: List[List[str]] | None = None,
    ) -> None:
        self.values = values or []
        self.title = "Test Worksheet"
        self.updated_ranges: list[str] = []

    def get_all_values(self) -> List[List[str]]:
        return self.values

    def update(
        self,
        *,
        range_name: str,
        values: List[List[str]],
        value_input_option: str,
    ) -> None:
        self.updated_ranges.append(range_name)

        start = range_name.split(":")[0]

        row_text = "".join(
            character
            for character in start
            if character.isdigit()
        )

        start_row = int(row_text)

        while len(self.values) < start_row - 1:
            self.values.append([])

        for index, row in enumerate(values):
            target_index = start_row - 1 + index

            while len(self.values) <= target_index:
                self.values.append([])

            self.values[target_index] = row


def make_service() -> GoogleSheetsService:
    service = object.__new__(
        GoogleSheetsService
    )

    return service


def test_empty_worksheet_initializes_headers_at_row_one() -> None:
    service = make_service()

    worksheet = FakeWorksheet()

    headers = [
        "Run Date",
        "Role",
        "Company",
    ]

    rows = [
        [
            "2026-08-13",
            "Data Analyst",
            "Stripe",
        ]
    ]

    written = service._append_aligned_rows(
        worksheet=worksheet,
        headers=headers,
        rows=rows,
        worksheet_label="Test Worksheet",
    )

    assert written == 1

    assert worksheet.values == [
        headers,
        rows[0],
    ]

    assert worksheet.updated_ranges == [
        "A1:C1",
        "A2:C2",
    ]


def test_second_export_appends_immediately_after_existing_data() -> None:
    service = make_service()

    headers = [
        "Run Date",
        "Role",
        "Company",
    ]

    worksheet = FakeWorksheet(
        values=[
            headers,
            [
                "2026-08-13",
                "Data Analyst",
                "Stripe",
            ],
        ]
    )

    rows = [
        [
            "2026-08-14",
            "Data Analyst",
            "Datadog",
        ]
    ]

    written = service._append_aligned_rows(
        worksheet=worksheet,
        headers=headers,
        rows=rows,
        worksheet_label="Test Worksheet",
    )

    assert written == 1

    assert worksheet.values == [
        headers,
        [
            "2026-08-13",
            "Data Analyst",
            "Stripe",
        ],
        [
            "2026-08-14",
            "Data Analyst",
            "Datadog",
        ],
    ]

    assert worksheet.updated_ranges == [
        "A3:C3",
    ]


def test_existing_blank_rows_are_not_treated_as_data() -> None:
    service = make_service()

    headers = [
        "Run Date",
        "Role",
        "Company",
    ]

    worksheet = FakeWorksheet(
        values=[
            headers,
            [
                "2026-08-13",
                "Data Analyst",
                "Stripe",
            ],
            [],
            [],
        ]
    )

    rows = [
        [
            "2026-08-14",
            "Data Analyst",
            "Datadog",
        ]
    ]

    written = service._append_aligned_rows(
        worksheet=worksheet,
        headers=headers,
        rows=rows,
        worksheet_label="Test Worksheet",
    )

    assert written == 1

    assert worksheet.updated_ranges == [
        "A3:C3",
    ]


def test_header_mismatch_fails_loudly() -> None:
    service = make_service()

    worksheet = FakeWorksheet(
        values=[
            [
                "Old Header",
                "Company",
            ]
        ]
    )

    headers = [
        "Run Date",
        "Role",
        "Company",
    ]

    rows = [
        [
            "2026-08-13",
            "Data Analyst",
            "Stripe",
        ]
    ]

    with pytest.raises(
        ValueError,
        match="Header mismatch",
    ):
        service._append_aligned_rows(
            worksheet=worksheet,
            headers=headers,
            rows=rows,
            worksheet_label="Test Worksheet",
        )


def test_row_width_mismatch_fails_before_data_write() -> None:
    service = make_service()

    worksheet = FakeWorksheet()

    headers = [
        "Run Date",
        "Role",
        "Company",
    ]

    rows = [
        [
            "2026-08-13",
            "Data Analyst",
        ]
    ]

    with pytest.raises(
        ValueError,
        match="has 2 columns",
    ):
        service._append_aligned_rows(
            worksheet=worksheet,
            headers=headers,
            rows=rows,
            worksheet_label="Test Worksheet",
        )

    assert worksheet.updated_ranges == [
        "A1:C1",
    ]


def test_empty_rows_do_not_modify_worksheet() -> None:
    service = make_service()

    worksheet = FakeWorksheet()

    written = service._append_aligned_rows(
        worksheet=worksheet,
        headers=[
            "Run Date",
            "Role",
            "Company",
        ],
        rows=[],
        worksheet_label="Test Worksheet",
    )

    assert written == 0
    assert worksheet.values == []
    assert worksheet.updated_ranges == []