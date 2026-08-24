from __future__ import annotations

import base64
import os
from typing import Any

from job_search_automation.application.queue import (
    ApplicationQueueItem,
)
from job_search_automation.services.http_client import (
    HttpClient,
)


class N8nApplicationHandler:
    """
    Application execution adapter for a locally hosted n8n webhook.

    Architecture:

        ApplicationExecutor
                ↓
        N8nApplicationHandler
                ↓
        HttpClient
                ↓
        Local n8n Webhook
                ↓
        n8n Application Workflow

    This adapter contains no browser or ATS logic.

    Configuration is supplied through environment variables:

        N8N_WEBHOOK_URL
        N8N_WEBHOOK_TOKEN
        N8N_WEBHOOK_TIMEOUT

    Optional Basic Authentication:

        N8N_BASIC_AUTH_USER
        N8N_BASIC_AUTH_PASSWORD

    Example:

        N8N_WEBHOOK_URL=http://127.0.0.1:5678/webhook/job-application
        N8N_WEBHOOK_TOKEN=
        N8N_WEBHOOK_TIMEOUT=30
    """

    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        *,
        webhook_url: str | None = None,
        webhook_token: str | None = None,
        basic_auth_user: str | None = None,
        basic_auth_password: str | None = None,
        timeout: float | None = None,
        http_client: HttpClient | None = None,
    ) -> None:
        self.webhook_url = (
            webhook_url.strip()
            if webhook_url is not None
            else os.getenv(
                "N8N_WEBHOOK_URL",
                "",
            ).strip()
        )

        self.webhook_token = (
            webhook_token
            if webhook_token is not None
            else os.getenv(
                "N8N_WEBHOOK_TOKEN",
                "",
            ).strip()
        )

        self.basic_auth_user = (
            basic_auth_user
            if basic_auth_user is not None
            else os.getenv(
                "N8N_BASIC_AUTH_USER",
                "",
            ).strip()
        )

        self.basic_auth_password = (
            basic_auth_password
            if basic_auth_password is not None
            else os.getenv(
                "N8N_BASIC_AUTH_PASSWORD",
                "",
            )
        )

        configured_timeout = os.getenv(
            "N8N_WEBHOOK_TIMEOUT",
            "",
        ).strip()

        if timeout is not None:
            self.timeout = float(timeout)

        elif configured_timeout:
            self.timeout = float(
                configured_timeout
            )

        else:
            self.timeout = self.DEFAULT_TIMEOUT

        self.http_client = (
            http_client
            or HttpClient(
                timeout=self.timeout
            )
        )

    # ==========================================================
    # PUBLIC HANDLER CONTRACT
    # ==========================================================

    def __call__(
        self,
        item: ApplicationQueueItem,
    ) -> dict[str, Any]:
        """
        Execute one application queue item through n8n.

        The returned dictionary is intentionally compatible with
        ApplicationExecutor.
        """

        if not isinstance(
            item,
            ApplicationQueueItem,
        ):
            raise TypeError(
                "item must be an ApplicationQueueItem"
            )

        self._validate_configuration()

        payload = self.build_payload(item)

        headers = self._build_headers()

        response = self.http_client.post(
            self.webhook_url,
            headers=headers,
            json=payload,
        )

        return self._normalise_response(
            response,
            item,
        )

    # ==========================================================
    # PAYLOAD
    # ==========================================================

    def build_payload(
        self,
        item: ApplicationQueueItem,
    ) -> dict[str, Any]:
        """
        Build the stable Python → n8n application contract.

        n8n should receive one canonical queue item rather than
        provider-specific or internal Python objects.
        """

        return {
            "event": "job_application",
            "version": "1.0",
            "job": {
                "job_id": str(
                    getattr(
                        item,
                        "job_id",
                        "",
                    )
                    or ""
                ),
                "title": str(
                    getattr(
                        item,
                        "title",
                        "",
                    )
                    or ""
                ),
                "company": str(
                    getattr(
                        item,
                        "company",
                        "",
                    )
                    or ""
                ),
                "location": str(
                    getattr(
                        item,
                        "location",
                        "",
                    )
                    or ""
                ),
                "job_url": str(
                    getattr(
                        item,
                        "job_url",
                        "",
                    )
                    or ""
                ),
                "provider": str(
                    getattr(
                        item,
                        "provider",
                        "",
                    )
                    or ""
                ),
                "source": str(
                    getattr(
                        item,
                        "source",
                        "",
                    )
                    or ""
                ),
                "searched_role": str(
                    getattr(
                        item,
                        "searched_role",
                        "",
                    )
                    or ""
                ),
                "overall_score": self._number(
                    getattr(
                        item,
                        "overall_score",
                        None,
                    )
                ),
                "score": self._number(
                    getattr(
                        item,
                        "score",
                        None,
                    )
                ),
                "selection_bucket": self._enum(
                    getattr(
                        item,
                        "selection_bucket",
                        None,
                    )
                ),
            },
            "application": {
                "readiness_decision": self._enum(
                    getattr(
                        item,
                        "readiness_decision",
                        None,
                    )
                ),
                "queue_status": self._enum(
                    getattr(
                        item,
                        "queue_status",
                        None,
                    )
                ),
                "decision": self._enum(
                    getattr(
                        item,
                        "decision",
                        None,
                    )
                ),
                "status": self._enum(
                    getattr(
                        item,
                        "status",
                        None,
                    )
                ),
                "eligible": bool(
                    getattr(
                        item,
                        "eligible",
                        False,
                    )
                ),
                "reason": str(
                    getattr(
                        item,
                        "reason",
                        "",
                    )
                    or ""
                ),
                "resume_tailoring_required": bool(
                    getattr(
                        item,
                        "resume_tailoring_required",
                        False,
                    )
                ),
                "notes": self._list(
                    getattr(
                        item,
                        "notes",
                        None,
                    )
                ),
                "recommended_actions": self._list(
                    getattr(
                        item,
                        "recommended_actions",
                        None,
                    )
                ),
                "application_url": str(
                    getattr(
                        item,
                        "application_url",
                        "",
                    )
                    or ""
                ),
            },
        }

    # ==========================================================
    # HEADERS
    # ==========================================================

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.webhook_token:
            headers["Authorization"] = (
                f"Bearer {self.webhook_token}"
            )

        if (
            self.basic_auth_user
            and self.basic_auth_password
        ):
            credentials = (
                f"{self.basic_auth_user}:"
                f"{self.basic_auth_password}"
            )

            encoded = base64.b64encode(
                credentials.encode("utf-8")
            ).decode("ascii")

            headers["Authorization"] = (
                f"Basic {encoded}"
            )

        return headers

    # ==========================================================
    # RESPONSE
    # ==========================================================

    @classmethod
    def _normalise_response(
        cls,
        response: Any,
        item: ApplicationQueueItem,
    ) -> dict[str, Any]:
        """
        Convert the n8n response into ApplicationExecutor's
        handler contract.
        """

        if response is None:
            response = {}

        if not isinstance(
            response,
            dict,
        ):
            raise TypeError(
                "n8n webhook response must be a JSON object."
            )

        status = str(
            response.get(
                "status",
                "SUBMITTED",
            )
            or "SUBMITTED"
        ).upper()

        message = str(
            response.get(
                "message",
                "n8n application workflow completed.",
            )
            or ""
        )

        metadata = response.get(
            "metadata",
            {},
        )

        if metadata is None:
            metadata = {}

        if not isinstance(
            metadata,
            dict,
        ):
            raise TypeError(
                "n8n response metadata must be a JSON object."
            )

        metadata = dict(metadata)

        metadata.setdefault(
            "executor",
            "n8n",
        )

        metadata.setdefault(
            "webhook",
            cls._safe_webhook_marker(
                item
            ),
        )

        return {
            "status": status,
            "message": message,
            "metadata": metadata,
        }

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def _validate_configuration(self) -> None:
        if not self.webhook_url:
            raise RuntimeError(
                (
                    "N8N_WEBHOOK_URL is not configured. "
                    "Set it to the local n8n webhook URL, "
                    "for example "
                    "'http://127.0.0.1:5678/webhook/job-application'."
                )
            )

        if not (
            self.webhook_url.startswith(
                "http://"
            )
            or self.webhook_url.startswith(
                "https://"
            )
        ):
            raise RuntimeError(
                "N8N_WEBHOOK_URL must use http:// or https://."
            )

        if self.timeout <= 0:
            raise RuntimeError(
                "N8N_WEBHOOK_TIMEOUT must be greater than zero."
            )

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _enum(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(
            getattr(
                value,
                "value",
                value,
            )
            or ""
        )

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _list(
        value: Any,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                str(item)
                for item in value
                if item is not None
            ]

        return [str(value)]

    @staticmethod
    def _safe_webhook_marker(
        item: ApplicationQueueItem,
    ) -> str:
        """
        Store only a non-sensitive execution marker in metadata.

        The complete webhook URL is deliberately not returned.
        """

        return (
            f"n8n:{str(getattr(item, 'job_id', '') or '')}"
        )