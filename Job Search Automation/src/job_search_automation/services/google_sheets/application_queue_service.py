from __future__ import annotations

from typing import Iterable

from job_search_automation.application.queue import (
    ApplicationQueueItem,
)
from job_search_automation.services import logger
from job_search_automation.services.google_sheets.google_sheets_service import (
    GoogleSheetsService,
)
from job_search_automation.services.google_sheets.application_queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
    application_queue_item_to_row,
)


class ApplicationQueueSheetsService:
    """
    Application Queue Sheets adapter.

    GoogleSheetsService owns all Google Sheets I/O.

    This adapter owns only:
        - ApplicationQueueItem -> row transformation
        - Application Queue export orchestration

    It does NOT:
        - search jobs
        - evaluate jobs
        - decide readiness
        - submit applications
        - perform direct gspread I/O
    """

    DEFAULT_WORKSHEET_NAME = "Application Queue"

    def __init__(
        self,
        sheets_service: GoogleSheetsService,
        worksheet_name: str | None = None,
    ) -> None:
        self.sheets_service = sheets_service

        self.worksheet_name = (
            worksheet_name
            or self.DEFAULT_WORKSHEET_NAME
        )

        # GoogleSheetsService owns worksheet creation and access.
        # The adapter must not perform independent worksheet lookup.
        self.worksheet = (
            sheets_service.application_queue_worksheet
        )

        logger.info(
            "Application Queue Sheets adapter ready for worksheet '%s'.",
            self.worksheet_name,
        )

    # ==========================================================
    # SHEET STATE
    # ==========================================================

    def row_count(self) -> int:
        return (
            self.sheets_service.application_queue_row_count()
        )

    def has_headers(self) -> bool:
        return (
            self.sheets_service.application_queue_has_headers()
        )

    def write_headers(self) -> None:
        self.sheets_service.write_application_queue_headers(
            APPLICATION_QUEUE_HEADERS
        )

        logger.info(
            "Application Queue headers validated."
        )

    # ==========================================================
    # EXPORT
    # ==========================================================

    def append_items(
        self,
        items: Iterable[ApplicationQueueItem],
    ) -> int:
        """
        Append application queue items.

        All Google Sheets writes are delegated to
        GoogleSheetsService.
        """

        items = list(items)

        if not items:
            logger.info(
                "No application queue items available."
            )
            return 0

        rows = [
            application_queue_item_to_row(item)
            for item in items
        ]

        logger.info(
            "Uploading %d application queue rows.",
            len(rows),
        )

        self.sheets_service.append_application_queue(
            headers=APPLICATION_QUEUE_HEADERS,
            rows=rows,
        )

        logger.info(
            "Successfully uploaded %d application queue rows.",
            len(rows),
        )

        return len(rows)

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self) -> None:
        self.sheets_service.clear_application_queue()