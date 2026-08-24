from __future__ import annotations

from typing import Protocol

from job_search_automation.application.queue import (
    ApplicationQueueItem,
)
from job_search_automation.application.queue_mapper import (
    APPLICATION_QUEUE_HEADERS,
    application_queue_rows,
)


class ApplicationQueueSheetWriter(Protocol):
    """
    Minimal Google Sheets contract required by the exporter.
    """

    def append_application_queue(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> None:
        ...


class ApplicationQueueSheetsExporter:
    """
    Export ApplicationQueueItem objects to the
    dedicated Application Queue worksheet.
    """

    def __init__(
        self,
        writer: ApplicationQueueSheetWriter,
    ) -> None:
        self.writer = writer

    def export(
        self,
        items: list[ApplicationQueueItem],
    ) -> int:
        if not items:
            return 0

        rows = application_queue_rows(
            items
        )

        if len(rows) != len(items):
            raise ValueError(
                "Application Queue row count does not "
                "match queue item count."
            )

        expected_columns = len(
            APPLICATION_QUEUE_HEADERS
        )

        for index, row in enumerate(
            rows,
            start=1,
        ):
            if len(row) != expected_columns:
                raise ValueError(
                    "Application Queue row "
                    f"{index} has {len(row)} columns; "
                    f"expected {expected_columns}."
                )

        self.writer.append_application_queue(
            headers=APPLICATION_QUEUE_HEADERS,
            rows=rows,
        )

        return len(rows)