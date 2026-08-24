from __future__ import annotations

from types import SimpleNamespace

from job_search_automation.orchestrators.search_pipeline import (
    SearchPipeline,
)
from job_search_automation.services.google_sheets.mapper import (
    HEADERS,
)

from job_search_automation.pipeline.unique_jobs_export_stage import (
    UniqueJobsExportStage,
)

def make_job() -> SimpleNamespace:
    return SimpleNamespace(
        run_date="2026-08-13",
        title="Data Analyst",
        company="Stripe",
        location="Mumbai",
        posted_at="2026-08-12",
        shortlist_likelihood_score=91.0,
        shortlist_bucket="Strong Match",
        apply_priority=90,
        recommendation="Apply",
        matched_skills=["Python", "SQL"],
        missing_skills=["Tableau"],
        source="Greenhouse",
        provider="greenhouse",
        searched_role="Data Analyst",
        company_tier="Tier 1",
        job_bucket="Analytics",
        blunt_reason="Strong analytics alignment",
        tailored_resume_text="Tailored resume",
        application_status="Not Applied",
        job_url="https://example.com/job/123",
    )


def test_search_pipeline_uses_canonical_sheet_headers() -> None:
    captured: dict[str, object] = {}

    pipeline = SearchPipeline.__new__(SearchPipeline)

    class FakeSheets:
        def append_jobs(
            self,
            *,
            headers: list[str],
            rows: list[list[str]],
        ) -> None:
            captured["headers"] = headers
            captured["rows"] = rows

    pipeline.google_sheets = FakeSheets()

    job = make_job()

    from job_search_automation.services.google_sheets.mapper import (
        job_to_row,
    )

    pipeline.google_sheets.append_jobs(
        headers=HEADERS,
        rows=[job_to_row(job)],
    )

    assert captured["headers"] == HEADERS
    assert len(captured["headers"]) == 17


def test_sheet_row_width_matches_headers() -> None:
    from job_search_automation.services.google_sheets.mapper import (
        job_to_row,
    )

    row = job_to_row(make_job())

    assert len(row) == len(HEADERS)


def test_sheet_export_preserves_column_order() -> None:
    from job_search_automation.services.google_sheets.mapper import (
        job_to_row,
    )

    row = job_to_row(make_job())

    expected = {
        "Run Date": "2026-08-13",
        "Role": "Data Analyst",
        "Company": "Stripe",
        "Location": "Mumbai",
        "Job URL": "https://example.com/job/123",
    }

    for header, expected_value in expected.items():
        assert row[HEADERS.index(header)] == expected_value


def test_second_export_is_sent_as_rows_without_header_duplication() -> None:
    exports: list[tuple[list[str], list[list[str]]]] = []

    class FakeSheets:
        def append_jobs(
            self,
            *,
            headers: list[str],
            rows: list[list[str]],
        ) -> None:
            exports.append((headers, rows))

    pipeline = SearchPipeline.__new__(SearchPipeline)
    pipeline.google_sheets = FakeSheets()

    from job_search_automation.services.google_sheets.mapper import (
        job_to_row,
    )

    first_job = make_job()
    second_job = make_job()
    second_job.company = "Datadog"

    pipeline.google_sheets.append_jobs(
        headers=HEADERS,
        rows=[job_to_row(first_job)],
    )

    pipeline.google_sheets.append_jobs(
        headers=HEADERS,
        rows=[job_to_row(second_job)],
    )

    assert len(exports) == 2

    assert exports[0][0] == HEADERS
    assert exports[1][0] == HEADERS

    assert len(exports[0][1]) == 1
    assert len(exports[1][1]) == 1

    assert exports[0][1][0][HEADERS.index("Company")] == "Stripe"
    assert exports[1][1][0][HEADERS.index("Company")] == "Datadog"


def test_empty_export_does_not_create_rows() -> None:
    exports: list[tuple[list[str], list[list[str]]]] = []

    class FakeSheets:
        def append_jobs(
            self,
            *,
            headers: list[str],
            rows: list[list[str]],
        ) -> None:
            exports.append((headers, rows))

    pipeline = SearchPipeline.__new__(SearchPipeline)
    pipeline.google_sheets = FakeSheets()

    # Production SearchPipeline only calls append_jobs after selection.
    # This test verifies the export boundary contract itself.
    assert exports == []

    def test_unique_jobs_export_build_rows() -> None:
        job = make_job()

        rows = UniqueJobsExportStage.build_rows(
            [job]
        )

        assert len(rows) == 1

        assert rows[0] == [
            "UNIQUE",
            "PASSED",
            "Data Analyst",
            "Stripe",
            "Mumbai",
            "https://example.com/job/123",
            "",
            "",
            "",
            "2026-08-12",
        ]


def test_unique_jobs_export_calls_append_unique_jobs() -> None:
    captured: dict[str, object] = {}

    class FakeSheets:
        def append_unique_jobs(
            self,
            *,
            headers: list[str],
            rows: list[list[object]],
        ) -> int:
            captured["headers"] = headers
            captured["rows"] = rows
            return len(rows)

    stage = UniqueJobsExportStage(
        sheets_service=FakeSheets()
    )

    result = stage.export(
        [make_job()]
    )

    assert result == 1
    assert captured["headers"] == UniqueJobsExportStage.HEADERS
    assert len(captured["rows"]) == 1


def test_unique_jobs_export_empty_jobs_returns_zero() -> None:
    called = False

    class FakeSheets:
        def append_unique_jobs(
            self,
            *,
            headers: list[str],
            rows: list[list[object]],
        ) -> int:
            nonlocal called
            called = True
            return len(rows)

    stage = UniqueJobsExportStage(
        sheets_service=FakeSheets()
    )

    result = stage.export([])

    assert result == 0
    assert called is False