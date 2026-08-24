from __future__ import annotations

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import google.api_core.exceptions


# ==========================================================
# RETRY CONFIGURATION
# ==========================================================

MAX_RETRIES = 3

INITIAL_WAIT_SECONDS = 2

MAX_WAIT_SECONDS = 20


# ==========================================================
# RETRY DECORATOR
# ==========================================================

gemini_retry = retry(

    retry=retry_if_exception_type(

        (

            google.api_core.exceptions.ResourceExhausted,

            google.api_core.exceptions.ServiceUnavailable,

            google.api_core.exceptions.DeadlineExceeded,

            google.api_core.exceptions.InternalServerError,

            TimeoutError,

            ConnectionError,

        )

    ),

    wait=wait_exponential(

        multiplier=INITIAL_WAIT_SECONDS,

        min=INITIAL_WAIT_SECONDS,

        max=MAX_WAIT_SECONDS,

    ),

    stop=stop_after_attempt(

        MAX_RETRIES

    ),

    reraise=True,

)


# ==========================================================
# OPTIONAL BASE CLASS
# ==========================================================

class RetryableGeminiClient:
    """
    Convenience base class.

    Subclasses simply decorate API methods with:

        @gemini_retry

    to automatically gain exponential retry behavior.
    """

    pass