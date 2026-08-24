from __future__ import annotations

from datetime import UTC, datetime, timedelta

from job_search_automation.config.scoring_rules import (
    SEARCH_LIMITS,
)
from job_search_automation.intelligence.freshness.job_freshness import (
    JobFreshnessEvaluator,
)


def main() -> None:
    print()
    print("=" * 70)
    print("FRESHNESS VALIDATION")
    print("=" * 70)

    evaluator = JobFreshnessEvaluator()

    now = datetime.now(UTC)

    print(
        f"[INFO] max_days_old="
        f"{SEARCH_LIMITS['max_days_old']}"
    )

    result_1 = evaluator.evaluate(
        posted_at=now - timedelta(hours=12),
        now=now,
    )

    assert result_1.accepted
    assert result_1.score == 100.0

    print(
        "[PASS] Jobs within 24 hours accepted."
    )

    result_2 = evaluator.evaluate(
        posted_at=now - timedelta(days=2),
        now=now,
    )

    assert result_2.accepted
    assert result_2.score == 90.0

    print(
        "[PASS] Jobs within 72 hours accepted."
    )

    result_3 = evaluator.evaluate(
        posted_at=now - timedelta(days=5),
        now=now,
    )

    assert result_3.accepted
    assert result_3.score == 70.0

    print(
        "[PASS] Jobs within 7 days accepted."
    )

    result_4 = evaluator.evaluate(
        posted_at=now - timedelta(days=8),
        now=now,
    )

    assert not result_4.accepted
    assert result_4.score == 0.0

    print(
        "[PASS] Jobs older than 7 days rejected."
    )

    result_5 = evaluator.evaluate(
        posted_at=None,
        now=now,
    )

    assert not result_5.accepted
    assert result_5.age_days is None

    print(
        "[PASS] Missing posted date rejected."
    )

    print()
    print("=" * 70)
    print("FRESHNESS VALIDATION PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()