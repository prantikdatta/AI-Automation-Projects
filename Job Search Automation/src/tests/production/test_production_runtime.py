from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_search_pipeline_imports():
    from job_search_automation.orchestrators.search_pipeline import (
        SearchPipeline,
    )

    assert SearchPipeline is not None


def test_final_selection_engine_imports():
    from job_search_automation.intelligence.final_selector import (
        FinalSelectionEngine,
    )

    assert FinalSelectionEngine is not None


def test_resume_matcher_imports():
    from job_search_automation.intelligence.resume_matcher import (
        ResumeMatcher,
    )

    assert ResumeMatcher is not None


def test_search_pipeline_exposes_run():
    from job_search_automation.orchestrators.search_pipeline import (
        SearchPipeline,
    )

    assert callable(
        getattr(
            SearchPipeline,
            "run",
            None,
        )
    )


def test_final_selection_engine_exposes_select():
    from job_search_automation.intelligence.final_selector import (
        FinalSelectionEngine,
    )

    engine = FinalSelectionEngine()

    assert callable(
        getattr(
            engine,
            "select",
            None,
        )
    )


def test_resume_matcher_exposes_match():
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