from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.execution import (
    ApplicationExecutor,
)
from job_search_automation.application.execution_audit import (
    ApplicationExecutionAudit,
)
from job_search_automation.application.n8n_handler import (
    N8nApplicationHandler,
)
from job_search_automation.application.queue import (
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


SEPARATOR = "=" * 80


class ValidationFailure(AssertionError):
    """Raised when a production orchestration invariant fails."""


class ValidationHttpClient:
    """
    Non-network HTTP boundary used to validate the production
    ApplicationExecutor -> N8nApplicationHandler contract.

    No real n8n request is made.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "url": url,
                "headers": headers or {},
                "json": json or {},
            }
        )

        return {
            "status": "SUBMITTED",
            "message": (
                "Synthetic n8n application workflow completed."
            ),
            "metadata": {
                "validation": True,
            },
        }


class ValidationState:
    def __init__(self) -> None:
        self.collected = 0
        self.enriched = 0
        self.evaluated = 0
        self.selected = 0
        self.exported = 0
        self.providers: dict[str, int] = {}
        self.sheet_headers: list[Any] = []
        self.sheet_rows: list[Any] = []


def fail(message: str) -> None:
    raise ValidationFailure(message)


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        fail(message)


def wrap_method(
    obj: Any,
    name: str,
    callback,
) -> None:
    original = getattr(obj, name)

    def wrapped(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = original(
            *args,
            **kwargs,
        )

        callback(
            result,
            *args,
            **kwargs,
        )

        return result

    setattr(
        obj,
        name,
        wrapped,
    )


def validate_search_response(
    response: SearchResponse,
) -> list[Job]:
    print(
        "[1/8] Validating real SearchPipeline response"
    )

    require(
        isinstance(response, SearchResponse),
        (
            "SearchPipeline.run() must return SearchResponse; "
            f"got {type(response).__name__}."
        ),
    )

    require(
        response.success is True,
        f"SearchPipeline returned success={response.success!r}.",
    )

    jobs = response.jobs

    require(
        isinstance(jobs, list),
        "SearchResponse.jobs must be a list.",
    )

    require(
        len(jobs) > 0,
        "Production SearchPipeline returned zero final jobs.",
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        require(
            isinstance(job, Job),
            (
                f"SearchResponse.jobs[{index - 1}] "
                f"is not a Job."
            ),
        )

        require(
            bool(str(job.title).strip()),
            f"Final job #{index} has no title.",
        )

        require(
            bool(str(job.company).strip()),
            f"Final job #{index} has no company.",
        )

        require(
            bool(str(job.location).strip()),
            f"Final job #{index} has no location.",
        )

        require(
            bool(str(job.job_url).strip()),
            f"Final job #{index} has no job_url.",
        )

        require(
            bool(str(job.provider).strip()),
            f"Final job #{index} has no provider.",
        )

        require(
            job.overall_score is not None,
            f"Final job #{index} has no overall_score.",
        )

        score = float(job.overall_score)

        require(
            0.0 <= score <= 100.0,
            (
                f"Final job #{index} has invalid "
                f"overall_score={score}."
            ),
        )

        require(
            job.final_selection_eligible is True,
            (
                f"Final job #{index} is not marked "
                "final_selection_eligible."
            ),
        )

    print(
        f"      PASS: {len(jobs)} final Job objects returned."
    )

    return jobs


def main() -> int:
    print(SEPARATOR)
    print("PRODUCTION APPLICATION ORCHESTRATION VALIDATION")
    print(SEPARATOR)
    print()
    print(
        "Real SearchPipeline is used."
    )
    print(
        "Google Sheets and n8n external side effects are captured."
    )
    print(
        "No real application submission is performed."
    )
    print()

    state = ValidationState()

    try:
        print(
            "[0/8] Creating real SearchPipeline"
        )

        pipeline = SearchPipeline()

        print(
            "      PASS: real SearchPipeline created."
        )
        print()

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
                        or getattr(
                            job,
                            "source",
                            "",
                        )
                        or "Unknown"
                    )
                    .strip()
                )

                state.providers[provider] = (
                    state.providers.get(
                        provider,
                        0,
                    )
                    + 1
                )

        def after_enrich(
            *_: Any,
            **__: Any,
        ) -> None:
            state.enriched += 1

        def after_evaluate(
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

        def capture_sheet_export(
            *,
            headers: Any,
            rows: Any,
        ) -> None:
            state.sheet_headers = list(
                headers or []
            )

            state.sheet_rows = list(
                rows or []
            )

            state.exported = len(
                state.sheet_rows
            )

        pipeline.google_sheets.append_jobs = (
            capture_sheet_export
        )

        print(
            "[1/8] Running real SearchPipeline"
        )

        response = pipeline.run()

        jobs = validate_search_response(
            response
        )

        print()

        print(
            "[2/8] Validating production pipeline stage counts"
        )

        require(
            state.collected > 0,
            "Zero jobs collected by SearchOrchestrator.",
        )

        require(
            state.enriched > 0,
            "Zero jobs reached enrichment.",
        )

        require(
            state.evaluated > 0,
            "Zero jobs reached ResumeMatcher.",
        )

        require(
            state.selected == len(jobs),
            (
                "FinalSelection count does not match "
                "SearchResponse.jobs."
            ),
        )

        print(
            f"      collected : {state.collected}"
        )

        print(
            f"      enriched  : {state.enriched}"
        )

        print(
            f"      evaluated : {state.evaluated}"
        )

        print(
            f"      selected  : {state.selected}"
        )

        print(
            "      PASS: production pipeline stages are connected."
        )
        print()

        print(
            "[3/8] Validating final-selection output"
        )

        scores = [
            float(job.overall_score)
            for job in jobs
        ]

        require(
            scores == sorted(
                scores,
                reverse=True,
            ),
            "Final jobs are not sorted by descending overall_score.",
        )

        urls = [
            str(job.job_url)
            .strip()
            .lower()
            .rstrip("/")
            for job in jobs
        ]

        require(
            len(urls) == len(set(urls)),
            "Duplicate final job URLs remain.",
        )

        print(
            "      PASS: final-selection output is coherent."
        )
        print()

        print(
            "[4/8] Running real ApplicationWorkflow"
        )

        workflow = ApplicationWorkflow()

        workflow_result = workflow.process(
            jobs,
            export_to_sheets=False,
        )

        require(
            workflow_result.evaluated == len(jobs),
            (
                "ApplicationWorkflow evaluated count does not "
                "match final jobs."
            ),
        )

        require(
            len(workflow_result.queue_items)
            == len(jobs),
            (
                "ApplicationWorkflow queue size does not "
                "match final jobs."
            ),
        )

        print(
            f"      queue_items: "
            f"{len(workflow_result.queue_items)}"
        )

        print(
            f"      actionable : "
            f"{workflow_result.queued}"
        )

        print(
            f"      manual     : "
            f"{workflow_result.manual_review}"
        )

        print(
            f"      rejected   : "
            f"{workflow_result.rejected}"
        )

        print(
            "      PASS: real ApplicationWorkflow processed "
            "the final jobs."
        )
        print()

        print(
            "[5/8] Validating ApplicationReadiness -> Queue"
        )

        for index, item in enumerate(
            workflow_result.queue_items,
            start=1,
        ):
            require(
                item.job_id,
                f"Queue item #{index} has no job_id.",
            )

            require(
                item.title,
                f"Queue item #{index} has no title.",
            )

            require(
                item.company,
                f"Queue item #{index} has no company.",
            )

            require(
                item.job_url,
                f"Queue item #{index} has no job_url.",
            )

            if item.queue_status in {
                ApplicationQueueStatus.READY,
                ApplicationQueueStatus.READY_WITH_TAILORING,
            }:
                require(
                    item.eligible is True,
                    (
                        f"Executable queue item #{index} "
                        "is not eligible."
                    ),
                )

            elif item.queue_status in {
                ApplicationQueueStatus.MANUAL_REVIEW,
                ApplicationQueueStatus.REJECTED,
            }:
                require(
                    item.eligible is False,
                    (
                        f"Non-executable queue item #{index} "
                        "is incorrectly eligible."
                    ),
                )

            else:
                fail(
                    (
                        f"Queue item #{index} has unknown "
                        f"queue_status={item.queue_status!r}."
                    )
                )

        print(
            "      PASS: readiness and queue contracts are valid."
        )
        print()

        print(
            "[6/8] Validating ApplicationExecutor boundary"
        )

        executable_items = [
            item
            for item in workflow_result.queue_items
            if item.queue_status
            in {
                ApplicationQueueStatus.READY,
                ApplicationQueueStatus.READY_WITH_TAILORING,
            }
        ]

        print(
            f"      executable items: "
            f"{len(executable_items)}"
        )

        if not executable_items:
            print(
                "      PASS: no executable production items "
                "were generated; no application was submitted."
            )
            print(
                "      Execution boundary correctly has nothing "
                "to execute."
            )

        else:
            validation_http = ValidationHttpClient()

            handler = N8nApplicationHandler(
                webhook_url=(
                    "http://127.0.0.1:5678/"
                    "webhook-test/job-application"
                ),
                http_client=validation_http,
            )

            executor = ApplicationExecutor(
                handler=handler,
            )

            results = executor.execute_many(
                executable_items
            )

            require(
                len(results)
                == len(executable_items),
                (
                    "ApplicationExecutor result count does "
                    "not match executable queue count."
                ),
            )

            for result in results:
                require(
                    result.status == "SUBMITTED",
                    (
                        "Synthetic n8n execution did not "
                        f"return SUBMITTED: {result.status!r}"
                    ),
                )

                require(
                    result.metadata.get("executor")
                    == "n8n",
                    "Execution metadata executor is not n8n.",
                )

            require(
                len(validation_http.calls)
                == len(executable_items),
                (
                    "HTTP call count does not match executable "
                    "queue count."
                ),
            )

            print(
                f"      executed: {len(results)}"
            )

            print(
                "      PASS: executable queue items crossed "
                "the ApplicationExecutor -> n8n boundary."
            )

        print()

        print(
            "[7/8] Validating execution audit"
        )

        if executable_items:
            for item, result in zip(
                executable_items,
                results,
            ):
                audit = ApplicationExecutionAudit(
                    job_id=item.job_id,
                )

                audit.mark_ready(
                    message=(
                        "Production orchestration "
                        "validation ready."
                    ),
                    metadata={
                        "executor": "n8n",
                        "validation": True,
                    },
                )

                audit.mark_submitted(
                    message=result.message,
                    metadata=result.metadata,
                )

                require(
                    audit.status
                    == ApplicationExecutionAudit.SUBMITTED,
                    (
                        f"Audit for {item.job_id} "
                        "did not reach SUBMITTED."
                    ),
                )

                payload = audit.to_dict()

                require(
                    payload["job_id"]
                    == item.job_id,
                    "Audit job_id changed during serialization.",
                )

                require(
                    payload["status"]
                    == "SUBMITTED",
                    "Audit status serialization is invalid.",
                )

            print(
                "      PASS: all executed items reached SUBMITTED audit."
            )

        else:
            print(
                "      PASS: no execution audit required because "
                "the production queue contained zero executable items."
            )

        print()

        print(
            "[8/8] Validating Google Sheets side-effect boundary"
        )

        require(
            isinstance(
                state.sheet_headers,
                list,
            ),
            "Captured Sheets headers are not a list.",
        )

        require(
            isinstance(
                state.sheet_rows,
                list,
            ),
            "Captured Sheets rows are not a list.",
        )

        print(
            f"      captured rows: {state.exported}"
        )

        print(
            "      PASS: Sheets boundary remains externally captured."
        )
        print()

        print(SEPARATOR)
        print(
            "PRODUCTION APPLICATION ORCHESTRATION "
            "VALIDATION PASSED"
        )
        print(SEPARATOR)
        print()
        print(
            f"collected       : {state.collected}"
        )
        print(
            f"enriched        : {state.enriched}"
        )
        print(
            f"evaluated       : {state.evaluated}"
        )
        print(
            f"selected        : {state.selected}"
        )
        print(
            f"queue_items     : {len(workflow_result.queue_items)}"
        )
        print(
            f"actionable      : {workflow_result.queued}"
        )
        print(
            f"manual_review   : {workflow_result.manual_review}"
        )
        print(
            f"rejected        : {workflow_result.rejected}"
        )
        print(
            f"executed        : {len(executable_items)}"
        )
        print(
            f"sheets_captured : {state.exported}"
        )

        return 0

    except Exception as exc:
        print()
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())