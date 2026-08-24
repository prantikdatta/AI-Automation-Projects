from __future__ import annotations

"""
Preflight validation before the first full RapidAPI + Apify production run.

No external API calls are made. Secrets are never printed.
"""

import importlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dotenv import load_dotenv

ENV_PATH = REPO_ROOT / ".env"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def value(name: str) -> str:
    return os.getenv(name, "").strip()


def main() -> None:
    print("=" * 80)
    print("PRODUCTION PROVIDER READINESS VALIDATION")
    print("=" * 80)
    print("External API calls: NONE")
    print()

    print("[1/4] Environment")

    require(
        ENV_PATH.exists(),
        f"Missing .env: {ENV_PATH}",
    )

    load_dotenv(
        ENV_PATH,
        override=False,
    )

    required = (
        "RAPIDAPI_KEY",
        "RAPIDAPI_HOST",
        "APIFY_API_TOKEN",
        "APIFY_ACTOR_ID",
        "GEMINI_API_KEY",
        "GOOGLE_SHEET_ID",
        "MASTER_RESUME_PATH",
    )

    missing = [
        name
        for name in required
        if not value(name)
    ]

    require(
        not missing,
        "Missing required environment values: "
        + ", ".join(missing),
    )

    placeholders = [
        name
        for name in required
        if value(name).lower()
        in {
            "changeme",
            "change_me",
            "your_key",
            "your_api_key",
        }
        or value(name).startswith("<")
        or value(name).lower().startswith("paste_")
    ]

    require(
        not placeholders,
        "Placeholder values remain for: "
        + ", ".join(placeholders),
    )

    print(f"      PASS: {ENV_PATH}")

    print("[2/4] Provider configuration")

    require(
        value("RAPIDAPI_HOST")
        == "jsearch.p.rapidapi.com",
        "RAPIDAPI_HOST must be "
        "'jsearch.p.rapidapi.com'.",
    )

    require(
        bool(value("APIFY_ACTOR_ID")),
        "APIFY_ACTOR_ID is empty.",
    )

    require(
        bool(value("GOOGLE_SHEET_ID")),
        "GOOGLE_SHEET_ID is empty.",
    )

    print(
        f"      RapidAPI host : "
        f"{value('RAPIDAPI_HOST')}"
    )

    print(
        f"      Apify actor   : "
        f"{value('APIFY_ACTOR_ID')}"
    )

    print(
        f"      Google Sheet  : "
        f"{value('GOOGLE_SHEET_ID')}"
    )

    print("      PASS")

    print("[3/4] Provider/runtime imports")

    modules = (
        "apify_client",
        "httpx",
        "tenacity",
        "job_search_automation.clients.rapidapi_client",
        "job_search_automation.providers.rapidapi_provider",
        "job_search_automation.orchestrators.search_pipeline",
    )

    failures = []

    for module_name in modules:
        try:
            importlib.import_module(
                module_name
            )
        except Exception as exc:
            failures.append(
                f"{module_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    require(
        not failures,
        "Import validation failed:\n"
        + "\n".join(failures),
    )

    print("      PASS")

    print("[4/4] Resume/runtime input")

    resume = Path(
        value("MASTER_RESUME_PATH")
    )

    if not resume.is_absolute():
        resume = REPO_ROOT / resume

    require(
        resume.exists(),
        f"Resume not found: {resume}",
    )

    require(
        resume.is_file(),
        f"Resume path is not a file: {resume}",
    )

    require(
        resume.stat().st_size > 0,
        f"Resume is empty: {resume}",
    )

    print(
        f"      Resume : {resume}"
    )

    print("      PASS")

    print()
    print("=" * 80)
    print("PRODUCTION PROVIDER READINESS VALIDATION PASSED")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()
        print("=" * 80)
        print("PRODUCTION PROVIDER READINESS VALIDATION FAILED")
        print("=" * 80)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print("=" * 80)
        raise