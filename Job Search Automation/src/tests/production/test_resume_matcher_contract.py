from __future__ import annotations


def test_resume_matcher_exposes_match_and_evaluate():
    from job_search_automation.intelligence.resume_matcher import (
        ResumeMatcher,
    )

    matcher = ResumeMatcher()

    assert callable(
        getattr(
            matcher,
            "match",
            None,
        )
    )

    assert callable(
        getattr(
            matcher,
            "evaluate",
            None,
        )
    )


def test_resume_matcher_match_delegates_to_evaluate():
    from job_search_automation.intelligence.resume_matcher import (
        ResumeMatcher,
    )

    matcher = ResumeMatcher()

    class DummyJob:
        pass

    expected = object()

    matcher.evaluate = lambda job: expected

    result = matcher.match(
        DummyJob()
    )

    assert result is expected