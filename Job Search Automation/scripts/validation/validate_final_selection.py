from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from job_search_automation.intelligence.final_selector import (
    FinalSelectionEngine,
)
from job_search_automation.models.job import Job


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def make_job(
    *,
    title: str,
    location: str,
    score: float,
    remote: bool = False,
) -> Job:
    return Job(
        searched_role=title,
        title=title,
        company="Validation Company",
        location=location,
        description="Validation job",
        job_url="https://example.com/job",
        source="validation",
        provider="validation",
        overall_score=score,
        remote=remote,
    )


def main() -> None:
    engine = FinalSelectionEngine()

    jobs = [
        make_job(
            title="Senior Data Analyst",
            location="Mumbai",
            score=85.0,
        ),
        make_job(
            title="Analytics Engineer",
            location="Bengaluru",
            score=68.0,
        ),
        make_job(
            title="Business Analyst",
            location="Hyderabad",
            score=58.0,
        ),
        make_job(
            title="Product Analyst",
            location="Remote India",
            score=70.0,
        ),
        make_job(
            title="Technical Program Manager",
            location="Mumbai",
            score=72.0,
        ),
        make_job(
            title="Credit Risk Analyst",
            location="Mumbai",
            score=74.0,
        ),
        make_job(
            title="Software Engineer",
            location="Mumbai",
            score=95.0,
        ),
        make_job(
            title="Data Analyst",
            location="New York",
            score=95.0,
        ),
        make_job(
            title="Data Analyst",
            location="Mumbai",
            score=40.0,
        ),
    ]

    selected = engine.select(jobs)

    print("=" * 80)
    print("FINAL SELECTION VALIDATION")
    print("=" * 80)

    for job in jobs:
        print(
            f"{job.title:40} | "
            f"{job.location:20} | "
            f"score={job.overall_score:6.2f} | "
            f"eligible={str(job.final_selection_eligible):5} | "
            f"bucket={job.final_selection_bucket}"
        )

    print("-" * 80)
    print(f"Input jobs     : {len(jobs)}")
    print(f"Selected jobs  : {len(selected)}")
    print(f"Rejected jobs  : {len(jobs) - len(selected)}")
    print("=" * 80)

    require(
        len(selected) == 6,
        (
            "Expected exactly 6 validation jobs to survive "
            "final selection."
        ),
    )

    require(
        any(
            job.final_selection_bucket == "Apply Now"
            for job in selected
        ),
        "No Apply Now job survived validation.",
    )

    require(
        any(
            job.final_selection_bucket == "Strong Match"
            for job in selected
        ),
        "No Strong Match job survived validation.",
    )

    require(
        any(
            job.final_selection_bucket == "Review"
            for job in selected
        ),
        "No Review job survived validation.",
    )

    print("FINAL SELECTION VALIDATION PASSED")


if __name__ == "__main__":
    main()