from __future__ import annotations

from typing import List

import gspread
from google.oauth2.service_account import Credentials

from job_search_automation.config.settings import settings
from job_search_automation.services import logger
from job_search_automation.services.google_sheets.mapper import HEADERS


class GoogleSheetsService:
    """
    Production Google Sheets service.

    Responsibilities:
        - connect to the configured spreadsheet
        - create required worksheets
        - initialize and validate worksheet headers
        - append rows at deterministic positions
        - keep row/header alignment stable
        - provide worksheet health checks

    This service owns Google Sheets I/O only.

    It does NOT perform:
        - job scoring
        - job selection
        - readiness evaluation
        - queue business rules
        - application execution
    """

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    DEFAULT_AUDIT_WORKSHEET = "Pipeline Audit"
    DEFAULT_APPLICATION_QUEUE_WORKSHEET = "Application Queue"
    DEFAULT_UNIQUE_JOBS_WORKSHEET = "Unique Jobs"

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self) -> None:
        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE,
            scopes=self.SCOPES,
        )

        self.client = gspread.authorize(credentials)

        self.spreadsheet = self.client.open_by_key(
            settings.GOOGLE_SHEET_ID
        )

        # ------------------------------------------------------
        # Final Jobs worksheet
        # ------------------------------------------------------

        self.worksheet = self._get_or_create_worksheet(
            settings.GOOGLE_WORKSHEET_NAME
        )

        # IMPORTANT:
        # Initialize/validate the canonical Jobs headers immediately.
        # This guarantees that row 1 is always the table header before
        # any validation or append operation occurs.
        self._ensure_headers(
            self.worksheet,
            HEADERS,
            self.worksheet.title,
        )

        # ------------------------------------------------------
        # Pipeline Audit worksheet
        # ------------------------------------------------------

        self.audit_worksheet = self._get_or_create_worksheet(
            getattr(
                settings,
                "GOOGLE_AUDIT_WORKSHEET_NAME",
                self.DEFAULT_AUDIT_WORKSHEET,
            )
        )

        # ------------------------------------------------------
        # Application Queue worksheet
        # ------------------------------------------------------

        self.application_queue_worksheet = (
            self._get_or_create_worksheet(
                getattr(
                    settings,
                    "GOOGLE_APPLICATION_QUEUE_WORKSHEET_NAME",
                    self.DEFAULT_APPLICATION_QUEUE_WORKSHEET,
                )
            )
        )

        logger.info(
            "Connected to Google Sheet '%s'.",
            settings.GOOGLE_WORKSHEET_NAME,
        )

        logger.info(
            "Pipeline audit worksheet '%s' ready.",
            self.audit_worksheet.title,
        )

        logger.info(
            "Application queue worksheet '%s' ready.",
            self.application_queue_worksheet.title,
        )

        # ------------------------------------------------------
        # Unique Jobs worksheet
        # ------------------------------------------------------

        self.unique_jobs_worksheet = (
            self._get_or_create_worksheet(
                getattr(
                    settings,
                    "GOOGLE_UNIQUE_JOBS_WORKSHEET_NAME",
                    self.DEFAULT_UNIQUE_JOBS_WORKSHEET,
                )
            )
        )

    # ==========================================================
    # WORKSHEET MANAGEMENT
    # ==========================================================

    def _get_or_create_worksheet(
        self,
        worksheet_name: str,
    ):
        try:
            return self.spreadsheet.worksheet(
                worksheet_name
            )

        except gspread.WorksheetNotFound:
            logger.info(
                "Worksheet '%s' not found. Creating it.",
                worksheet_name,
            )

            return self.spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=5000,
                cols=100,
            )

    # ==========================================================
    # GENERIC SHEET HELPERS
    # ==========================================================

    @staticmethod
    def _column_letter(column_number: int) -> str:
        """
        Convert a 1-based column number to an Excel/Sheets
        column letter.
        """

        if column_number < 1:
            raise ValueError(
                "column_number must be >= 1"
            )

        result = ""

        while column_number:
            column_number, remainder = divmod(
                column_number - 1,
                26,
            )

            result = (
                chr(65 + remainder)
                + result
            )

        return result

    @classmethod
    def _range_for_rows(
        cls,
        start_row: int,
        row_count: int,
        column_count: int,
    ) -> str:
        """
        Build an explicit Google Sheets range.

        Example:
            start_row=2
            row_count=4
            column_count=8

        Returns:
            A2:H5
        """

        if start_row < 1:
            raise ValueError(
                "start_row must be >= 1"
            )

        if row_count < 1:
            raise ValueError(
                "row_count must be >= 1"
            )

        if column_count < 1:
            raise ValueError(
                "column_count must be >= 1"
            )

        end_row = (
            start_row
            + row_count
            - 1
        )

        end_column = cls._column_letter(
            column_count
        )

        return (
            f"A{start_row}:"
            f"{end_column}{end_row}"
        )

    @staticmethod
    def _normalise_row(
        row: List[str],
    ) -> List[str]:
        """
        Convert all row values to strings while preserving
        column order.
        """

        return [
            "" if value is None else str(value)
            for value in row
        ]

    @classmethod
    def _normalise_headers(
        cls,
        headers: List[str],
    ) -> List[str]:
        return cls._normalise_row(
            headers
        )

    @staticmethod
    def _row_has_content(
        row: List[str],
    ) -> bool:
        return any(
            str(value).strip()
            for value in row
        )

    def _all_values(
        self,
        worksheet,
    ) -> List[List[str]]:
        """
        Retrieve the complete logical contents of a worksheet.
        """

        values = worksheet.get_all_values()

        if not values:
            return []

        return [
            self._normalise_row(row)
            for row in values
        ]

    def _next_append_row(
        self,
        worksheet,
    ) -> int:
        """
        Determine the deterministic next row for data.

        row 1 = header
        data begins at row 2
        append occurs immediately after the last non-empty row.
        """

        values = self._all_values(
            worksheet
        )

        if not values:
            return 2

        last_content_row = 0

        for index, row in enumerate(
            values,
            start=1,
        ):
            if self._row_has_content(row):
                last_content_row = index

        if last_content_row < 1:
            return 2

        return max(
            last_content_row + 1,
            2,
        )

    def _ensure_headers(
        self,
        worksheet,
        headers: List[str],
        worksheet_label: str,
    ) -> None:
        """
        Establish and validate the canonical header row.

        Rules:

            1. Empty worksheet:
               write headers explicitly to row 1.

            2. Existing worksheet with matching headers:
               continue.

            3. Existing worksheet with different headers:
               fail loudly.

        Existing headers are never silently overwritten.
        """

        canonical_headers = (
            self._normalise_headers(headers)
        )

        if not canonical_headers:
            raise ValueError(
                f"Cannot initialize '{worksheet_label}' "
                "with an empty header list."
            )

        values = self._all_values(
            worksheet
        )

        # ------------------------------------------------------
        # Empty worksheet -> initialize row 1.
        # ------------------------------------------------------

        if not values or not self._row_has_content(values[0]):
            end_column = self._column_letter(
                len(canonical_headers)
            )

            header_range = (
                f"A1:{end_column}1"
            )

            worksheet.update(
                range_name=header_range,
                values=[canonical_headers],
                value_input_option="RAW",
            )

            logger.info(
                "Initialized headers for '%s' at row 1.",
                worksheet_label,
            )

            return

        # ------------------------------------------------------
        # Existing worksheet -> validate row 1.
        # ------------------------------------------------------

        existing_headers = self._normalise_headers(
            values[0]
        )

        expected = canonical_headers

        if existing_headers != expected:
            raise ValueError(
                (
                    f"Header mismatch in worksheet "
                    f"'{worksheet_label}'. "
                    f"Expected={expected!r}; "
                    f"Found={existing_headers!r}."
                )
            )

        logger.info(
            "Validated existing headers for '%s'.",
            worksheet_label,
        )

    def _append_aligned_rows(
        self,
        worksheet,
        headers: List[str],
        rows: List[List[str]],
        worksheet_label: str,
    ) -> int:
        """
        Write rows to an explicit range directly beneath the
        existing dataset.

        Every row must have exactly the same number of cells
        as the header.
        """

        if not rows:
            logger.info(
                "No rows available for '%s'.",
                worksheet_label,
            )

            return 0

        canonical_headers = (
            self._normalise_headers(headers)
        )

        self._ensure_headers(
            worksheet,
            canonical_headers,
            worksheet_label,
        )

        expected_columns = len(
            canonical_headers
        )

        normalised_rows: List[List[str]] = []

        for index, row in enumerate(
            rows,
            start=1,
        ):
            normalised = self._normalise_row(
                row
            )

            if len(normalised) != expected_columns:
                raise ValueError(
                    (
                        f"Row #{index} in "
                        f"'{worksheet_label}' has "
                        f"{len(normalised)} columns, "
                        f"but the header has "
                        f"{expected_columns} columns."
                    )
                )

            normalised_rows.append(
                normalised
            )

        start_row = self._next_append_row(
            worksheet
        )

        target_range = self._range_for_rows(
            start_row=start_row,
            row_count=len(normalised_rows),
            column_count=expected_columns,
        )

        logger.info(
            (
                "Writing %d rows to '%s' "
                "at explicit range %s."
            ),
            len(normalised_rows),
            worksheet_label,
            target_range,
        )

        worksheet.update(
            range_name=target_range,
            values=normalised_rows,
            value_input_option="USER_ENTERED",
        )

        logger.info(
            (
                "Successfully wrote %d rows "
                "to '%s' at %s."
            ),
            len(normalised_rows),
            worksheet_label,
            target_range,
        )

        return len(normalised_rows)

    # ==========================================================
    # FINAL JOB WORKSHEET
    # ==========================================================

    def clear(self) -> None:
        logger.info(
            "Clearing worksheet '%s'.",
            self.worksheet.title,
        )

        self.worksheet.clear()

    def row_count(self) -> int:
        return len(
            self._all_values(
                self.worksheet
            )
        )

    def has_headers(self) -> bool:
        values = self._all_values(
            self.worksheet
        )

        return bool(
            values
            and self._row_has_content(values[0])
        )

    def write_headers(
        self,
        headers: List[str],
    ) -> None:
        self._ensure_headers(
            self.worksheet,
            headers,
            self.worksheet.title,
        )

    def append_job(
        self,
        row: List[str],
    ) -> None:
        """
        Append one final-job row.

        The canonical Jobs headers are used so a single-row
        export also preserves the production schema.
        """

        self._append_aligned_rows(
            worksheet=self.worksheet,
            headers=HEADERS,
            rows=[row],
            worksheet_label=self.worksheet.title,
        )

    def append_jobs(
        self,
        headers: List[str],
        rows: List[List[str]],
    ) -> None:
        """
        Append final jobs beneath the existing dataset.

        Header behavior:
            - initialize row 1 if worksheet is empty
            - validate row 1 if worksheet already contains data

        Row behavior:
            - every row must match header width
            - rows are written to one explicit contiguous range
            - no Google Sheets append-table detection is used
        """

        self._append_aligned_rows(
            worksheet=self.worksheet,
            headers=headers,
            rows=rows,
            worksheet_label=self.worksheet.title,
        )

        # ==========================================================
    # UNIQUE JOBS WORKSHEET
    # ==========================================================

    def append_unique_jobs(
        self,
        headers: List[str],
        rows: List[List[str]],
    ) -> int:
        """
        Append deduplicated jobs captured before freshness filtering.

        This worksheet has its own schema and is intentionally kept
        separate from:
            - final Jobs worksheet
            - Pipeline Audit worksheet
            - Application Queue worksheet

        Business rules remain outside GoogleSheetsService.
        """

        return self._append_aligned_rows(
            worksheet=self.unique_jobs_worksheet,
            headers=headers,
            rows=rows,
            worksheet_label=self.unique_jobs_worksheet.title,
        )

    # ==========================================================
    # PIPELINE AUDIT WORKSHEET
    # ==========================================================

    def clear_audit(self) -> None:
        logger.info(
            "Clearing audit worksheet '%s'.",
            self.audit_worksheet.title,
        )

        self.audit_worksheet.clear()

    def audit_row_count(self) -> int:
        return len(
            self._all_values(
                self.audit_worksheet
            )
        )

    def audit_has_headers(self) -> bool:
        values = self._all_values(
            self.audit_worksheet
        )

        return bool(
            values
            and self._row_has_content(values[0])
        )

    def write_audit_headers(
        self,
        headers: List[str],
    ) -> None:
        self._ensure_headers(
            self.audit_worksheet,
            headers,
            self.audit_worksheet.title,
        )

    def append_audit_rows(
        self,
        headers: List[str],
        rows: List[List[str]],
    ) -> None:
        self._append_aligned_rows(
            worksheet=self.audit_worksheet,
            headers=headers,
            rows=rows,
            worksheet_label=self.audit_worksheet.title,
        )

    # ==========================================================
    # APPLICATION QUEUE WORKSHEET
    # ==========================================================

    def clear_application_queue(self) -> None:
        logger.info(
            "Clearing application queue worksheet '%s'.",
            self.application_queue_worksheet.title,
        )

        self.application_queue_worksheet.clear()

    def application_queue_row_count(self) -> int:
        return len(
            self._all_values(
                self.application_queue_worksheet
            )
        )

    def application_queue_has_headers(self) -> bool:
        values = self._all_values(
            self.application_queue_worksheet
        )

        return bool(
            values
            and self._row_has_content(values[0])
        )

    def write_application_queue_headers(
        self,
        headers: List[str],
    ) -> None:
        self._ensure_headers(
            self.application_queue_worksheet,
            headers,
            self.application_queue_worksheet.title,
        )

    def append_application_queue(
        self,
        headers: List[str],
        rows: List[List[str]],
    ) -> None:
        """
        Append application-ready queue items.

        This method performs only schema/header/alignment
        enforcement.

        Business rules remain in ApplicationQueueBuilder /
        ApplicationReadiness / ApplicationWorkflow.
        """

        self._append_aligned_rows(
            worksheet=self.application_queue_worksheet,
            headers=headers,
            rows=rows,
            worksheet_label=self.application_queue_worksheet.title,
        )

    # ==========================================================
    # HEALTH CHECK
    # ==========================================================

    def health_check(self) -> bool:
        try:
            self.worksheet.acell("A1")
            self.audit_worksheet.acell("A1")
            self.application_queue_worksheet.acell("A1")
            self.unique_jobs_worksheet.acell("A1")

            return True

        except Exception:
            logger.exception(
                "Google Sheets health check failed."
            )

            return False