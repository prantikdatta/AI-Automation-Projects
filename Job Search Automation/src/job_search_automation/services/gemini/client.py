from __future__ import annotations

import httpx

from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from job_search_automation.config import settings


class GeminiUnavailableError(RuntimeError):
    """
    Raised when Gemini is unavailable for the current pipeline run.

    Gemini quota/rate-limit exhaustion is treated as a provider-level
    availability failure rather than a pipeline-fatal error.
    """


class GeminiClient:
    """
    Client for the Google Gemini API.

    Runtime behaviour
    -----------------
    - Transient network errors may be retried.
    - HTTP 429 is NOT retried.
    - Once HTTP 429 is received, Gemini is disabled for the lifetime
      of this client instance.
    - Subsequent Gemini calls fail immediately without making HTTP
      requests.
    - The API key is sent through a request header rather than the URL
      so it is not exposed in HTTP error URLs or logs.
    """

    BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models"
    )

    def __init__(self) -> None:

        self.api_key = settings.GEMINI_API_KEY

        self.model = settings.GEMINI_MODEL

        self.client = httpx.Client(
            timeout=60,
        )

        # ----------------------------------------------------------
        # Provider circuit breaker
        # ----------------------------------------------------------
        #
        # Once Gemini returns HTTP 429, no additional Gemini calls
        # are attempted during this client instance's lifetime.
        #
        # The pipeline can therefore continue to downstream stages
        # such as scoring, selection and Google Sheets export.
        #
        self._disabled = False

        self._disabled_reason: str | None = None

    # ==============================================================
    # PROVIDER AVAILABILITY
    # ==============================================================

    @property
    def available(self) -> bool:
        """
        Return whether Gemini is currently available.
        """

        return not self._disabled

    def _disable(
        self,
        reason: str,
    ) -> None:
        """
        Disable Gemini for the current client instance.
        """

        self._disabled = True

        self._disabled_reason = reason

    def _ensure_available(self) -> None:
        """
        Fail immediately when Gemini has already been disabled.
        """

        if self._disabled:

            reason = (
                self._disabled_reason
                or "Gemini is unavailable."
            )

            raise GeminiUnavailableError(
                reason
            )

    # ==============================================================
    # GENERATE
    # ==============================================================

    @retry(
        retry=retry_if_exception_type(
            httpx.RequestError,
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=2,
            min=2,
            max=10,
        ),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate Gemini content.

        HTTP 429 is intentionally NOT included in the retry policy.
        It disables Gemini immediately for this client instance.
        """

        self._ensure_available()

        url = (
            f"{self.BASE_URL}/"
            f"{self.model}:generateContent"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        }

        try:

            response = self.client.post(
                url,
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        except httpx.RequestError:
            # Network-level errors are handled by Tenacity.
            raise

        # ----------------------------------------------------------
        # GEMINI QUOTA / RATE LIMIT
        # ----------------------------------------------------------

        if response.status_code == 429:

            self._disable(
                "Gemini HTTP 429 quota/rate limit reached. "
                "Gemini enrichment is disabled for this pipeline run."
            )

            raise GeminiUnavailableError(
                self._disabled_reason
            )

        # ----------------------------------------------------------
        # OTHER HTTP ERRORS
        # ----------------------------------------------------------

        response.raise_for_status()

        # ----------------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------------

        data = response.json()

        candidates = data.get(
            "candidates",
            [],
        )

        if not candidates:

            raise GeminiUnavailableError(
                "Gemini returned no candidates."
            )

        content = candidates[0].get(
            "content",
            {},
        )

        parts = content.get(
            "parts",
            [],
        )

        if not parts:

            raise GeminiUnavailableError(
                "Gemini returned no response content."
            )

        text = parts[0].get(
            "text",
        )

        if not text:

            raise GeminiUnavailableError(
                "Gemini returned empty response text."
            )

        return text

    # ==============================================================
    # JOB ANALYSIS
    # ==============================================================

    def analyze_job(
        self,
        prompt: str,
    ) -> str:

        return self.generate(
            prompt
        )

    # ==============================================================
    # RESUME TAILORING
    # ==============================================================

    def tailor_resume(
        self,
        prompt: str,
    ) -> str:

        return self.generate(
            prompt
        )

    # ==============================================================
    # COVER LETTER
    # ==============================================================

    def generate_cover_letter(
        self,
        prompt: str,
    ) -> str:

        return self.generate(
            prompt
        )

    # ==============================================================
    # INTERVIEW QUESTIONS
    # ==============================================================

    def generate_interview_questions(
        self,
        prompt: str,
    ) -> str:

        return self.generate(
            prompt
        )

    # ==============================================================
    # CLOSE
    # ==============================================================

    def close(self) -> None:
        """
        Close the underlying HTTP client.
        """

        self.client.close()