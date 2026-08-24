from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from job_search_automation.application.execution import (
    ApplicationExecutor,
)
from job_search_automation.application.queue import (
    ApplicationQueueStatus,
)
from job_search_automation.application.workflow import (
    ApplicationWorkflow,
)
from job_search_automation.models.job import Job
from job_search_automation.models.response import SearchResponse
from job_search_automation.orchestrators.search_pipeline import SearchPipeline


class ValidationFailure(AssertionError):
    """Raised when a production application-workflow invariant fails."""


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise ValidationFailure(message)


def job_id(job: Job) -> str:
    for field in (
        "id",
        "job_id",
    ):
        value = getattr(
            job,
            field,
            None,
        )

        if value is not None and str(value).strip():
            return str(value).strip()

    job_url = getattr(
        job,
        "job_url",
        None,
    )

    if job_url is not None and str(job_url).strip():
        return str(job_url).strip()

    return (
        f"{str(getattr(job, 'company', '')).strip()}:"
        f"{str(getattr(job, 'title', '')).strip()}"
    )


def build_production_pipeline() -> SearchPipeline:
    """
    Build the real production SearchPipeline.

    No synthetic jobs are used here.
    """

    return SearchPipeline()


def validate_final_jobs(
    response: SearchResponse,
) -> list[Job]:
    print(
        "[1/8] Validating real SearchPipeline response"
    )

    require(
        isinstance(
            response,
            SearchResponse,
        ),
        (
            "SearchPipeline must return SearchResponse; "
            f"got {type(response).__name__}."
        ),
    )

    jobs = list(
        getattr(
            response,
            "jobs",
            [],
        )
        or []
    )

    require(
        jobs,
        "SearchPipeline returned zero final jobs.",
    )

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        require(
            isinstance(
                job,
                Job,
            ),
            f"Final job #{index} is not a Job model.",
        )

        require(
            bool(
                str(
                    getattr(
                        job,
                        "title",
                        "",
                    )
                ).strip()
            ),
            f"Final job #{index} has no title.",
        )

        require(
            bool(
                str(
                    getattr(
                        job,
                        "company",
                        "",
                    )
                ).strip()
            ),
            f"Final job #{index} has no company.",
        )

        require(
            bool(
                str(
                    getattr(
                        job,
                        "location",
                        "",
                    )
                ).strip()
            ),
            f"Final job #{index} has no location.",
        )

        require(
            bool(
                str(
                    getattr(
                        job,
                        "job_url",
                        "",
                    )
                ).strip()
            ),
            f"Final job #{index} has no job_url.",
        )

        require(
            getattr(
                job,
                "final_selection_eligible",
                False,
            )
            is True,
            (
                f"Final job #{index} is not marked "
                "final_selection_eligible=True."
            ),
        )

    print(
        f"      PASS: {len(jobs)} final Job objects returned."
    )

    return jobs


def validate_pipeline_counts(
    response: SearchResponse,
) -> None:
    print(
        "\n[2/8] Validating production pipeline stage counts"
    )

    jobs = list(
        getattr(
            response,
            "jobs",
            [],
        )
        or []
    )

    total_returned = getattr(
        response,
        "total_returned",
        None,
    )

    total_found = getattr(
        response,
        "total_found",
        None,
    )

    if total_returned is not None:
        require(
            int(total_returned) == len(jobs),
            (
                "SearchResponse.total_returned does not match "
                "final Job count."
            ),
        )

    if total_found is not None:
        require(
            int(total_found) == len(jobs),
            (
                "SearchResponse.total_found does not match "
                "final Job count."
            ),
        )

    print(
        f"      selected : {len(jobs)}"
    )

    if total_found is not None:
        print(
            f"      total_found : {total_found}"
        )

    if total_returned is not None:
        print(
            f"      total_returned : {total_returned}"
        )

    print(
        "      PASS: production pipeline final-output counts are coherent."
    )


def validate_final_selection(
    jobs: list[Job],
) -> None:
    print(
        "\n[3/8] Validating final-selection output"
    )

    urls = [
        str(
            getattr(
                job,
                "job_url",
                "",
            )
        ).strip().lower().rstrip("/")
        for job in jobs
    ]

    require(
        len(urls) == len(set(urls)),
        "Duplicate final job URLs remain.",
    )

    scores: list[float] = []

    for job in jobs:
        try:
            scores.append(
                float(
                    getattr(
                        job,
                        "overall_score",
                        0,
                    )
                    or 0
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValidationFailure(
                (
                    "Final job contains an invalid "
                    "overall_score."
                )
            )

    require(
        scores == sorted(
            scores,
            reverse=True,
        ),
        "Final jobs are not ranked by descending overall_score.",
    )

    print(
        "      PASS: final-selection output is coherent."
    )


def validate_application_workflow(
    jobs: list[Job],
) -> list[Any]:
    print(
        "\n[4/8] Running real ApplicationWorkflow"
    )

    workflow = ApplicationWorkflow()

    queue = workflow.build(
        jobs
    )

    require(
        isinstance(
            queue,
            list,
        ),
        (
            "ApplicationWorkflow must return a list; "
            f"got {type(queue).__name__}."
        ),
    )

    print(
        f"      final jobs       : {len(jobs)}"
    )

    print(
        f"      queue items      : {len(queue)}"
    )

    return queue


def validate_queue_mapping(
    jobs: list[Job],
    queue: list[Any],
) -> None:
    print(
        "\n[5/8] Validating final jobs -> application queue mapping"
    )

    final_ids = {
        job_id(job)
        for job in jobs
    }

    queue_ids: list[str] = []

    for index, item in enumerate(
        queue,
        start=1,
    ):
        require(
            hasattr(
                item,
                "job_id",
            ),
            f"Queue item #{index} has no job_id.",
        )

        current_id = str(
            item.job_id
        ).strip()

        require(
            current_id,
            f"Queue item #{index} has an empty job_id.",
        )

        queue_ids.append(
            current_id
        )

        require(
            current_id in final_ids,
            (
                f"Queue item #{index} references job "
                f"{current_id!r}, which is not in final jobs."
            ),
        )

    require(
        len(queue_ids) == len(set(queue_ids)),
        "ApplicationWorkflow produced duplicate queue job IDs.",
    )

    require(
        len(queue) <= len(jobs),
        (
            "ApplicationWorkflow produced more queue items "
            "than final selected jobs."
        ),
    )

    print(
        "      PASS: queue items are a valid subset of final jobs."
    )


def validate_readiness_distribution(
    queue: list[Any],
) -> None:
    print(
        "\n[6/8] Validating application-readiness distribution"
    )

    executable_statuses = {
        ApplicationQueueStatus.READY,
        ApplicationQueueStatus.READY_WITH_TAILORING,
    }

    manual_review_status = (
        ApplicationQueueStatus.MANUAL_REVIEW
    )

    rejected_status = (
        ApplicationQueueStatus.REJECTED
    )

    executable_count = 0
    manual_review_count = 0
    rejected_count = 0

    for item in queue:
        status = item.queue_status

        if status in executable_statuses:
            executable_count += 1

        elif status == manual_review_status:
            manual_review_count += 1

        elif status == rejected_status:
            rejected_count += 1

    require(
        executable_count
        + manual_review_count
        + rejected_count
        == len(queue),
        "Queue contains an unsupported queue status.",
    )

    print(
        f"      executable       : {executable_count}"
    )

    print(
        f"      manual_review    : {manual_review_count}"
    )

    print(
        f"      rejected         : {rejected_count}"
    )

    print(
        "      PASS: readiness states are valid."
    )


def validate_executable_subset(
    queue: list[Any],
) -> list[Any]:
    print(
        "\n[7/8] Validating executable application subset"
    )

    executable = [
        item
        for item in queue
        if item.queue_status
        in {
            ApplicationQueueStatus.READY,
            ApplicationQueueStatus.READY_WITH_TAILORING,
        }
    ]

    for index, item in enumerate(
        executable,
        start=1,
    ):
        require(
            bool(
                getattr(
                    item,
                    "eligible",
                    False,
                )
            ),
            (
                f"Executable queue item #{index} "
                "is not eligible."
            ),
        )

        require(
            item.queue_status
            in {
                ApplicationQueueStatus.READY,
                ApplicationQueueStatus.READY_WITH_TAILORING,
            },
            (
                f"Executable queue item #{index} "
                "has invalid queue_status."
            ),
        )

    print(
        f"      executable queue items: {len(executable)}"
    )

    print(
        "      PASS: only READY / READY_WITH_TAILORING items are executable."
    )

    return executable


def validate_execution_contract(
    executable: list[Any],
) -> None:
    print(
        "\n[8/8] Validating ApplicationExecutor contract"
    )

    executor = ApplicationExecutor()

    results = executor.execute_many(
        executable
    )

    require(
        len(results) == len(executable),
        (
            "ApplicationExecutor result count does not match "
            "executable queue count."
        ),
    )

    for index, result in enumerate(
        results,
        start=1,
    ):
        require(
            result.job_id
            == executable[index - 1].job_id,
            (
                f"Execution result #{index} job_id does not "
                "match queue item."
            ),
        )

        require(
            result.status
            in {
                "READY",
                "SUBMITTED",
            },
            (
                f"Execution result #{index} has unexpected "
                f"status={result.status!r}."
            ),
        )

    print(
        "      PASS: executable queue maps cleanly to ApplicationExecutor."
    )


def main() -> int:
    print("=" * 80)
    print(
        "PRODUCTION APPLICATION WORKFLOW -> EXECUTION VALIDATION"
    )
    print("=" * 80)
    print(
        "Using the real SearchPipeline, ApplicationWorkflow, "
        "ApplicationQueue and ApplicationExecutor."
    )
    print()

    try:
        pipeline = build_production_pipeline()

        response = pipeline.run()

        jobs = validate_final_jobs(
            response
        )

        validate_pipeline_counts(
            response
        )

        validate_final_selection(
            jobs
        )

        queue = validate_application_workflow(
            jobs
        )

        validate_queue_mapping(
            jobs,
            queue,
        )

        validate_readiness_distribution(
            queue
        )

        executable = validate_executable_subset(
            queue
        )

        validate_execution_contract(
            executable
        )

        print()
        print("=" * 80)
        print(
            "PRODUCTION APPLICATION WORKFLOW -> "
            "EXECUTION VALIDATION PASSED"
        )
        print("=" * 80)
        print()
        print(
            f"final jobs        : {len(jobs)}"
        )
        print(
            f"queue items       : {len(queue)}"
        )
        print(
            f"executable items  : {len(executable)}"
        )
        print()
        print(
            "IMPORTANT: queue size is intentionally NOT required "
            "to equal final-job count."
        )
        print(
            "MANUAL_REVIEW and REJECTED jobs remain non-executable."
        )

        return 0

    except Exception as exc:
        print()
        print("!" * 80)
        print("VALIDATION FAILED")
        print("!" * 80)
        print()
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )