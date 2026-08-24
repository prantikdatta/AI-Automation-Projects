from __future__ import annotations

from job_search_automation.intelligence.final_selector import (
    FinalSelectionEngine,
)

from job_search_automation.intelligence.resume_matcher import (
    ResumeMatcher,
)

from job_search_automation.orchestrators.search_pipeline import (
    SearchPipeline,
)


def test_final_selector_imports():
    assert FinalSelectionEngine is not None


def test_resume_matcher_imports():
    assert ResumeMatcher is not None


def test_search_pipeline_imports():
    assert SearchPipeline is not None


def test_final_selector_is_callable():
    assert callable(FinalSelectionEngine)


def test_resume_matcher_is_callable():
    assert callable(ResumeMatcher)


def test_search_pipeline_is_callable():
    assert callable(SearchPipeline)