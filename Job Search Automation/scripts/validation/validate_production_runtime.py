from __future__ import annotations

"""
Real production runtime validation.

Modes
-----
fake
    Runs the real SearchPipeline and ApplicationWorkflow, then exercises
    ApplicationExecutor with a deterministic local handler.

n8n
    Runs the real SearchPipeline and ApplicationWorkflow, then exercises
    ApplicationExecutor -> N8nApplicationHandler -> local n8n.

Important
---------
The real production run is never altered to manufacture an actionable job.

If the real production selection produces zero executable application
items, n8n mode uses a deterministic validation-only ApplicationQueueItem.
This exists solely to prove the Python -> n8n execution boundary.

The n8n workflow MUST be validation-only. It must not submit a real
application.

Required for --mode n8n
-----------------------
N8N_WEBHOOK_URL

Optional
--------
N8N_WEBHOOK_TOKEN
N8N_BASIC_AUTH_USER
N8N_BASIC_AUTH_PASSWORD
N8N_WEBHOOK_TIMEOUT
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from job_search_automation.application.execution import (
    ApplicationExecutor,
)
from job_search_automation.application.execution_audit import (
    ApplicationExecutionAuditStore,
)
from job_search_automation.application.n8n_handler import (
    N8nApplicationHandler,
)
from job_search_automation.application.queue import (
    ApplicationQueueItem,
    ApplicationQueueStatus,
)
from job_search_automation.application.workflow import (
    ApplicationWorkflow,
)
from job_search_automation.models.job import Job
from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import (
    SearchPipeline,
)


class ValidationState:
    """Counters captured from the real production pipeline."""

    def __init__(self) -> None:
        self.collected = 0
        self.enriched = 0
        self.evaluated = 0
        self.selected = 0

        self.job_sheet_headers: list[Any] = []
        self.job_sheet_rows: list[Any] = []
        self.job_sheet_exported = 0

        self.application_evaluated = 0
        self.application_queued = 0
        self.application_manual_review = 0
        self.application_rejected = 0

        self.execution_results = 0
        self.execution_audits = 0
        self.execution_calls = 0
        self.external_submissions = 0

        self.providers: dict[str, int] = {}


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def wrap_method(
    obj: Any,
    method_name: str,
    after: Callable[..., None],
) -> None:
    """Observe an existing production method without replacing its behavior."""

    original = getattr(obj, method_name)

    def wrapped(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = original(
            *args,
            **kwargs,
        )

        after(
            result,
            *args,
            **kwargs,
        )

        return result

    setattr(
        obj,
        method_name,
        wrapped,
    )


def status_value(
    item: Any,
) -> str:
    status = getattr(
        item,
        "queue_status",
        None,
    )

    value = getattr(
        status,
        "value",
        status,
    )

    return str(
        value or ""
    ).upper()


def validate_job(
    job: Job,
    index: int,
) -> None:
    require(
        isinstance(job, Job),
        f"Job #{index} is not a canonical Job model.",
    )

    for field_name in (
        "title",
        "company",
        "location",
        "job_url",
        "provider",
    ):
        require(
            bool(
                str(
                    getattr(
                        job,
                        field_name,
                        "",
                    )
                ).strip()
            ),
            f"Job #{index} has no {field_name}.",
        )

    require(
        job.overall_score is not None,
        f"Job #{index} has no overall_score.",
    )

    score = float(job.overall_score)

    require(
        0 <= score <= 100,
        f"Job #{index} has invalid overall_score={score}.",
    )

    require(
        job.resume_match_result is not None,
        f"Job #{index} has no resume_match_result.",
    )

    require(
        job.final_selection_eligible is True,
        f"Job #{index} is not final-selection eligible.",
    )

    require(
        job.final_selection_bucket
        not in (
            None,
            "",
            "Reject",
        ),
        (
            f"Job #{index} has invalid "
            f"final_selection_bucket="
            f"{job.final_selection_bucket!r}."
        ),
    )


def validate_application_queue_item(
    item: Any,
    index: int,
) -> None:
    require(
        item is not None,
        f"Application queue item #{index} is None.",
    )

    for field_name in (
        "job_id",
        "title",
        "company",
        "job_url",
    ):
        require(
            bool(
                str(
                    getattr(
                        item,
                        field_name,
                        "",
                    )
                ).strip()
            ),
            f"Application queue item #{index} has no {field_name}.",
        )

    require(
        status_value(item)
        in {
            "READY",
            "READY_WITH_TAILORING",
            "MANUAL_REVIEW",
            "REJECTED",
        },
        (
            f"Application queue item #{index} has "
            f"invalid queue status={status_value(item)!r}."
        ),
    )


def build_validation_queue_item() -> ApplicationQueueItem:
    """
    Deterministic READY item used only when the real production selection
    contains no executable application item.

    The item is intentionally identical in contract to the existing
    validate_local_n8n.py validation fixture.
    """

    return ApplicationQueueItem(
        job_id="n8n-local-validation-001",
        title="Senior Data Analyst",
        company="N8N Validation Company",
        location="Mumbai",
        job_url="https://example.com/n8n-local-validation-001",
        provider="validation",
        source="validation",
        searched_role="Data Analyst",
        overall_score=82.5,
        score=82.5,
        selection_bucket="A - Apply Now",
        readiness_decision="READY",
        queue_status=ApplicationQueueStatus.QUEUED,
        decision=ApplicationQueueStatus.QUEUED,
        status=ApplicationQueueStatus.QUEUED,
        eligible=True,
        reason="Deterministic n8n production-boundary validation item.",
        resume_tailoring_required=False,
        notes=[
            "Validation only.",
            "No real application submission.",
        ],
        recommended_actions=[
            "Do not submit a real application.",
        ],
        application_url=None,
        metadata={
            "validation_fixture": True,
            "external_submission": False,
        },
    )


def build_fake_handler(
    execution_calls: list[str],
) -> Callable[[Any], dict[str, Any]]:
    """Build a deterministic handler that performs no external action."""

    def fake_application_handler(
        item: Any,
    ) -> dict[str, Any]:
        execution_calls.append(
            str(item.job_id)
        )

        return {
            "status": "SUBMITTED",
            "message": "Fake application execution completed.",
            "metadata": {
                "executor": "production-runtime-fake",
                "external_submission": False,
                "validation": True,
            },
        }

    return fake_application_handler


def build_n8n_handler() -> N8nApplicationHandler:
    """Construct the real production N8nApplicationHandler."""

    webhook_url = os.getenv(
        "N8N_WEBHOOK_URL",
        "",
    ).strip()

    require(
        bool(webhook_url),
        "N8N_WEBHOOK_URL is required for --mode n8n.",
    )

    timeout_raw = os.getenv(
        "N8N_WEBHOOK_TIMEOUT",
        "30",
    ).strip()

    try:
        timeout = float(timeout_raw)
    except ValueError as exc:
        raise AssertionError(
            "N8N_WEBHOOK_TIMEOUT must be numeric."
        ) from exc

    require(
        timeout > 0,
        "N8N_WEBHOOK_TIMEOUT must be greater than zero.",
    )

    return N8nApplicationHandler(
        webhook_url=webhook_url,
        webhook_token=os.getenv(
            "N8N_WEBHOOK_TOKEN",
            "",
        ).strip(),
        basic_auth_user=os.getenv(
            "N8N_BASIC_AUTH_USER",
            "",
        ).strip(),
        basic_auth_password=os.getenv(
            "N8N_BASIC_AUTH_PASSWORD",
            "",
        ),
        timeout=timeout,
    )


def build_application_executor(
    mode: str,
    execution_calls: list[str],
) -> ApplicationExecutor:
    """Construct the real ApplicationExecutor for the selected mode."""

    if mode == "fake":
        return ApplicationExecutor(
            handler=build_fake_handler(
                execution_calls
            ),
        )

    if mode == "n8n":
        n8n_handler = build_n8n_handler()

        def n8n_execution_handler(
            item: Any,
        ) -> dict[str, Any]:
            execution_calls.append(
                str(item.job_id)
            )

            result = n8n_handler(item)

            require(
                isinstance(result, dict),
                "N8nApplicationHandler returned a non-dict result.",
            )

            return result

        return ApplicationExecutor(
            handler=n8n_execution_handler,
        )

    raise AssertionError(
        f"Unsupported validation mode={mode!r}."
    )


def validate_search_response(
    response: SearchResponse,
    state: ValidationState,
) -> None:
    require(
        isinstance(
            response,
            SearchResponse,
        ),
        (
            "SearchPipeline.run() did not return SearchResponse. "
            f"Received {type(response).__name__}."
        ),
    )

    require(
        response.success is True,
        (
            "SearchPipeline returned "
            f"success={response.success!r}."
        ),
    )

    require(
        state.collected > 0,
        "BLOCKER: zero jobs collected by the real search stack.",
    )

    require(
        state.enriched > 0,
        "BLOCKER: zero jobs reached enrichment.",
    )

    require(
        state.evaluated > 0,
        "BLOCKER: zero jobs reached ResumeMatcher.",
    )

    require(
        state.selected > 0,
        "BLOCKER: zero jobs survived final selection.",
    )

    require(
        len(response.jobs) == state.selected,
        (
            "SearchResponse.jobs does not match final selection: "
            f"response={len(response.jobs)}, "
            f"selected={state.selected}."
        ),
    )

    require(
        response.total_found == state.selected,
        (
            "SearchResponse.total_found is inconsistent: "
            f"total_found={response.total_found}, "
            f"selected={state.selected}."
        ),
    )

    require(
        response.total_returned == state.selected,
        (
            "SearchResponse.total_returned is inconsistent: "
            f"total_returned={response.total_returned}, "
            f"selected={state.selected}."
        ),
    )

    for index, job in enumerate(
        response.jobs,
        start=1,
    ):
        validate_job(
            job,
            index,
        )

    scores = [
        float(job.overall_score)
        for job in response.jobs
    ]

    require(
        scores == sorted(
            scores,
            reverse=True,
        ),
        "Final jobs are not ordered by overall_score descending.",
    )

    urls = [
        str(job.job_url)
        .strip()
        .lower()
        .rstrip("/")
        for job in response.jobs
    ]

    require(
        len(urls) == len(set(urls)),
        "Duplicate job URLs remain in final output.",
    )


def validate_job_sheet_export(
    response: SearchResponse,
    state: ValidationState,
) -> None:
    require(
        bool(state.job_sheet_headers),
        "Google Sheets export headers are empty.",
    )

    require(
        len(state.job_sheet_rows)
        == len(response.jobs),
        (
            "Google Sheets row count does not match "
            f"final jobs: rows={len(state.job_sheet_rows)}, "
            f"jobs={len(response.jobs)}."
        ),
    )

    for index, row in enumerate(
        state.job_sheet_rows,
        start=1,
    ):
        require(
            len(row)
            == len(state.job_sheet_headers),
            (
                f"Google Sheets row #{index} has "
                f"{len(row)} cells but "
                f"{len(state.job_sheet_headers)} headers."
            ),
        )


def validate_application_workflow(
    response: SearchResponse,
    state: ValidationState,
) -> list[Any]:
    print()
    print("=" * 90)
    print("APPLICATION WORKFLOW VALIDATION")
    print("=" * 90)

    workflow = ApplicationWorkflow()

    result = workflow.process(
        response.jobs,
        export_to_sheets=False,
    )

    state.application_evaluated = result.evaluated
    state.application_queued = result.queued
    state.application_manual_review = result.manual_review
    state.application_rejected = result.rejected

    items = result.queue_items

    require(
        state.application_evaluated
        == len(response.jobs),
        (
            "ApplicationWorkflow evaluated count does not match "
            f"final-selection count: evaluated={state.application_evaluated}, "
            f"selected={len(response.jobs)}."
        ),
    )

    require(
        isinstance(items, list),
        "ApplicationWorkflow.queue_items must be a list.",
    )

    for index, item in enumerate(
        items,
        start=1,
    ):
        validate_application_queue_item(
            item,
            index,
        )

    job_ids = {
        str(item.job_id).strip()
        for item in items
    }

    require(
        len(job_ids) == len(items),
        "Duplicate job IDs exist in the application queue.",
    )

    calculated_actionable = sum(
        1
        for item in items
        if status_value(item)
        in {
            "READY",
            "READY_WITH_TAILORING",
        }
    )

    calculated_manual = sum(
        1
        for item in items
        if status_value(item) == "MANUAL_REVIEW"
    )

    calculated_rejected = sum(
        1
        for item in items
        if status_value(item) == "REJECTED"
    )

    require(
        state.application_queued == calculated_actionable,
        (
            "ApplicationWorkflow queued count is inconsistent: "
            f"reported={state.application_queued}, "
            f"calculated={calculated_actionable}."
        ),
    )

    require(
        state.application_manual_review == calculated_manual,
        (
            "ApplicationWorkflow manual-review count is inconsistent: "
            f"reported={state.application_manual_review}, "
            f"calculated={calculated_manual}."
        ),
    )

    require(
        state.application_rejected == calculated_rejected,
        (
            "ApplicationWorkflow rejected count is inconsistent: "
            f"reported={state.application_rejected}, "
            f"calculated={calculated_rejected}."
        ),
    )

    selected_urls = {
        str(job.job_url)
        .strip()
        .lower()
        .rstrip("/")
        for job in response.jobs
    }

    queue_urls = {
        str(item.job_url)
        .strip()
        .lower()
        .rstrip("/")
        for item in items
    }

    require(
        queue_urls.issubset(selected_urls),
        (
            "Application queue contains a job that was not "
            "present in Final Selection."
        ),
    )

    require(
        len(queue_urls) == len(items),
        "Duplicate job URLs exist in the application queue.",
    )

    print(
        f"Application queue items : {len(items)}"
    )
    print(
        f"Actionable items         : {state.application_queued}"
    )
    print(
        f"Manual review items      : {state.application_manual_review}"
    )
    print(
        f"Rejected items           : {state.application_rejected}"
    )

    return items


def execute_application_boundary(
    mode: str,
    application_items: list[Any],
    state: ValidationState,
) -> None:
    print()
    print("=" * 90)
    print("APPLICATION EXECUTION VALIDATION")
    print("=" * 90)

    execution_calls: list[str] = []

    real_executable_items = [
        item
        for item in application_items
        if status_value(item)
        in {
            "READY",
            "READY_WITH_TAILORING",
        }
    ]

    execution_items = list(
        real_executable_items
    )

    fixture_used = False

    if not execution_items and mode == "n8n":
        execution_items = [
            build_validation_queue_item()
        ]
        fixture_used = True

        print(
            "Real production executable items : 0"
        )
        print(
            "Using deterministic n8n validation fixture."
        )
        print(
            "Fixture is NOT a production-selected job."
        )

    elif not execution_items:
        print(
            "Real production executable items : 0"
        )
        print(
            "No application execution is required in fake mode."
        )

    print(
        f"Execution items              : {len(execution_items)}"
    )

    application_executor = build_application_executor(
        mode,
        execution_calls,
    )

    execution_results = (
        application_executor.execute_many(
            execution_items
        )
    )

    audit_store = ApplicationExecutionAuditStore()

    audit_records = audit_store.record_many(
        execution_results,
        executor=(
            "production-runtime-fake"
            if mode == "fake"
            else "n8n"
        ),
    )

    state.execution_results = len(
        execution_results
    )

    state.execution_audits = len(
        audit_records
    )

    state.execution_calls = len(
        execution_calls
    )

    require(
        len(execution_results)
        == len(execution_items),
        (
            "Execution result count does not match execution item count: "
            f"results={len(execution_results)}, "
            f"items={len(execution_items)}."
        ),
    )

    require(
        len(audit_records)
        == len(execution_items),
        (
            "Execution audit count does not match execution item count: "
            f"audits={len(audit_records)}, "
            f"items={len(execution_items)}."
        ),
    )

    for item, result in zip(
        execution_items,
        execution_results,
    ):
        require(
            result.job_id == item.job_id,
            (
                "Execution result job_id mismatch: "
                f"queue={item.job_id!r}, "
                f"result={result.job_id!r}."
            ),
        )

        require(
            bool(str(result.status).strip()),
            (
                "Application execution returned an empty status "
                f"for {item.job_id!r}."
            ),
        )

        metadata = result.metadata

        require(
            isinstance(metadata, dict),
            (
                "Application execution metadata must be a dictionary "
                f"for {item.job_id!r}."
            ),
        )

        if mode == "fake":
            require(
                result.status == "SUBMITTED",
                (
                    "Fake execution did not return SUBMITTED for "
                    f"{item.job_id!r}: {result.status!r}."
                ),
            )

            require(
                metadata.get("external_submission") is False,
                (
                    "Fake execution result indicates an external "
                    "submission occurred."
                ),
            )

        else:
            require(
                metadata.get("executor") == "n8n",
                (
                    "n8n execution result does not identify "
                    "executor='n8n'."
                ),
            )

            require(
                metadata.get("external_submission") is not True,
                (
                    "BLOCKER: n8n execution result indicates that "
                    "an external application submission occurred."
                ),
            )

            if fixture_used:
                require(
                    metadata.get("validation_only") is True
                    or metadata.get("test") is True,
                    (
                        "n8n validation fixture did not receive a "
                        "validation-only response."
                    ),
                )

    require(
        len(execution_calls)
        == len(execution_items),
        (
            "Application handler invocation count does not match "
            f"execution item count: calls={len(execution_calls)}, "
            f"items={len(execution_items)}."
        ),
    )

    require(
        len(set(execution_calls))
        == len(execution_calls),
        "Duplicate application job IDs were executed.",
    )

    summary = audit_store.summary()

    if mode == "fake":
        expected_summary = (
            {
                "SUBMITTED": len(execution_items)
            }
            if execution_items
            else {}
        )
    else:
        expected_summary: dict[str, int] = {}

        for result in execution_results:
            status = str(result.status)

            expected_summary[status] = (
                expected_summary.get(
                    status,
                    0,
                )
                + 1
            )

    require(
        summary == expected_summary,
        (
            "Unexpected execution audit summary: "
            f"actual={summary!r}, "
            f"expected={expected_summary!r}."
        ),
    )

    print(
        f"Execution results            : {len(execution_results)}"
    )
    print(
        f"Execution audit records     : {len(audit_records)}"
    )
    print(
        f"Application handler calls   : {len(execution_calls)}"
    )
    print(
        "External submissions        : 0"
    )

    if mode == "fake":
        print(
            "PASS: fake production execution boundary validated."
        )
    elif fixture_used:
        print(
            "PASS: real Python -> n8n boundary validated "
            "using the deterministic validation fixture."
        )
    else:
        print(
            "PASS: real Python -> n8n boundary validated "
            "using a production-selected executable item."
        )


def main(
    mode: str = "fake",
) -> None:
    print("=" * 90)
    print("PRODUCTION RUNTIME VALIDATION")
    print("=" * 90)
    print(
        f"Execution mode          : {mode}"
    )
    print(
        "Real SearchPipeline     : YES"
    )
    print(
        "Real ApplicationWorkflow: YES"
    )
    print(
        "Real ApplicationExecutor: YES"
    )

    if mode == "fake":
        print(
            "Application boundary    : deterministic fake handler"
        )
    else:
        print(
            "Application boundary    : REAL N8nApplicationHandler"
        )
        print(
            "n8n workflow             : validation-only"
        )

    print()

    state = ValidationState()
    pipeline = SearchPipeline()

    def after_collect(
        jobs: list[Job],
        *_: Any,
        **__: Any,
    ) -> None:
        state.collected = len(jobs)

        for job in jobs:
            provider = (
                str(
                    getattr(
                        job,
                        "provider",
                        "",
                    )
                ).strip()
                or str(
                    getattr(
                        job,
                        "source",
                        "",
                    )
                ).strip()
                or "Unknown"
            )

            state.providers[provider] = (
                state.providers.get(
                    provider,
                    0,
                )
                + 1
            )

    def after_enrich(
        job: Job,
        *_: Any,
        **__: Any,
    ) -> None:
        state.enriched += 1

    def after_evaluate(
        result: Any,
        *_: Any,
        **__: Any,
    ) -> None:
        state.evaluated += 1

    def after_select(
        jobs: list[Job],
        *_: Any,
        **__: Any,
    ) -> None:
        state.selected = len(jobs)

    wrap_method(
        pipeline.search_orchestrator,
        "collect_jobs",
        after_collect,
    )

    wrap_method(
        pipeline.enrichment_pipeline,
        "process",
        after_enrich,
    )

    wrap_method(
        pipeline.resume_matcher,
        "evaluate",
        after_evaluate,
    )

    wrap_method(
        pipeline.final_selector,
        "select",
        after_select,
    )

    def capture_job_sheet_export(
        *,
        headers: Any,
        rows: Any,
    ) -> None:
        state.job_sheet_headers = list(
            headers or []
        )

        state.job_sheet_rows = list(
            rows or []
        )

        state.job_sheet_exported = len(
            state.job_sheet_rows
        )

    pipeline.google_sheets.append_jobs = (
        capture_job_sheet_export
    )

    print(
        "Executing real SearchPipeline..."
    )

    response = pipeline.run()

    validate_search_response(
        response,
        state,
    )

    validate_job_sheet_export(
        response,
        state,
    )

    application_items = validate_application_workflow(
        response,
        state,
    )

    execute_application_boundary(
        mode,
        application_items,
        state,
    )

    print()
    print("=" * 90)
    print("RUNTIME VALIDATION SUMMARY")
    print("=" * 90)

    print(
        f"Collected jobs          : {state.collected}"
    )
    print(
        f"Enriched jobs           : {state.enriched}"
    )
    print(
        f"Evaluated jobs          : {state.evaluated}"
    )
    print(
        f"Selected jobs           : {state.selected}"
    )
    print(
        f"Job Sheets rows         : {state.job_sheet_exported}"
    )
    print(
        f"Response jobs           : {len(response.jobs)}"
    )

    print()
    print("Provider contribution:")

    for provider, count in sorted(
        state.providers.items()
    ):
        print(
            f"  {provider:30s}: {count}"
        )

    print()
    print("Application workflow:")

    print(
        f"  Evaluated             : "
        f"{state.application_evaluated}"
    )
    print(
        f"  Actionable            : "
        f"{state.application_queued}"
    )
    print(
        f"  Manual Review         : "
        f"{state.application_manual_review}"
    )
    print(
        f"  Rejected              : "
        f"{state.application_rejected}"
    )

    print()
    print("Application execution:")

    print(
        f"  Mode                  : "
        f"{mode}"
    )
    print(
        f"  Execution results     : "
        f"{state.execution_results}"
    )
    print(
        f"  Audit records         : "
        f"{state.execution_audits}"
    )
    print(
        f"  Handler calls         : "
        f"{state.execution_calls}"
    )
    print(
        f"  External submissions : "
        f"{state.external_submissions}"
    )

    print()
    print("Final selected jobs:")

    for index, job in enumerate(
        response.jobs,
        start=1,
    ):
        print(
            f"  {index:03d} | "
            f"{job.title[:45]:45s} | "
            f"{job.company[:25]:25s} | "
            f"{job.location[:20]:20s} | "
            f"score={float(job.overall_score):6.2f} | "
            f"{job.final_selection_bucket}"
        )

    print()
    print("=" * 90)
    print("PRODUCTION RUNTIME VALIDATION PASSED")
    print("=" * 90)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Validate the real production search/application runtime."
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "fake",
            "n8n",
        ],
        default="fake",
        help=(
            "Application execution boundary to validate. "
            "Default: fake."
        ),
    )

    args = parser.parse_args()

    try:
        main(
            mode=args.mode,
        )

    except Exception as exc:
        print()
        print("=" * 90)
        print("PRODUCTION RUNTIME VALIDATION FAILED")
        print("=" * 90)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print("=" * 90)
        raise