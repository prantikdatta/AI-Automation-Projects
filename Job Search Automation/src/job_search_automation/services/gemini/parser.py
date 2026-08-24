from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from job_search_automation.services import logger
from job_search_automation.services.gemini.schemas import (
    GeminiResponse,
)


class GeminiParser:
    """
    Responsible for converting raw Gemini responses into
    strongly typed Pydantic models.

    Responsibilities
    ----------------
    • Remove markdown wrappers
    • Extract JSON
    • Parse JSON
    • Validate schema
    • Raise meaningful exceptions
    """

    # ======================================================
    # PUBLIC API
    # ======================================================

    def parse(
        self,
        response_text: str,
    ) -> GeminiResponse:

        cleaned = self._clean_response(
            response_text
        )

        payload = self._load_json(
            cleaned
        )

        return self._validate(
            payload
        )

    # ======================================================
    # CLEAN RESPONSE
    # ======================================================

    def _clean_response(
        self,
        text: str,
    ) -> str:

        text = text.strip()

        text = re.sub(
            r"^```json",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"^```",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"```$",
            "",
            text,
        )

        text = text.strip()

        start = text.find("{")

        end = text.rfind("}")

        if start == -1 or end == -1:

            raise ValueError(
                "No JSON object found in Gemini response."
            )

        return text[start : end + 1]

    # ======================================================
    # LOAD JSON
    # ======================================================

    def _load_json(
        self,
        cleaned_json: str,
    ) -> dict[str, Any]:

        try:

            return json.loads(
                cleaned_json
            )

        except json.JSONDecodeError as exc:

            logger.exception(
                "Invalid JSON returned by Gemini."
            )

            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

    # ======================================================
    # VALIDATE
    # ======================================================

    def _validate(
        self,
        payload: dict[str, Any],
    ) -> GeminiResponse:

        try:

            return GeminiResponse.model_validate(
                payload
            )

        except ValidationError as exc:

            logger.exception(
                "Gemini response failed schema validation."
            )

            raise ValueError(
                "Gemini response does not match schema."
            ) from exc

    # ======================================================
    # SAFE PARSE
    # ======================================================

    def safe_parse(
        self,
        response_text: str,
    ) -> GeminiResponse | None:
        """
        Never raises.

        Returns None if parsing fails.
        """

        try:

            return self.parse(
                response_text
            )

        except Exception:

            logger.exception(
                "Unable to parse Gemini response."
            )

            return None