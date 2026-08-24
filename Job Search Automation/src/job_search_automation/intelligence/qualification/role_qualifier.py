from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RoleQualificationResult:
    """
    Result of evaluating whether a job title belongs to the
    requested role family.

    Qualification is a HARD GATE.

    It does not determine:
        - resume match
        - score
        - employer quality
        - freshness
        - final application priority

    It only answers:

        "Is this job actually one of the requested roles?"
    """

    qualified: bool
    matched_role: str | None = None
    reason: str = ""


class RoleQualifier:
    """
    Determines whether a job title belongs to the requested role family.

    The qualifier deliberately works from the SearchRequest.roles list
    rather than hard-coding a single career path.

    This is important because the search profile is intentionally
    multi-role.
    """

    # ----------------------------------------------------------
    # Normalization
    # ----------------------------------------------------------

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower().strip()

        value = value.replace("&", " and ")

        value = re.sub(r"[^a-z0-9\s]", " ", value)

        value = re.sub(r"\s+", " ", value)

        return value.strip()

    # ----------------------------------------------------------
    # Tokenization
    # ----------------------------------------------------------

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        return set(cls._normalize(value).split())

    # ----------------------------------------------------------
    # Exact / phrase matching
    # ----------------------------------------------------------

    @classmethod
    def _phrase_match(
        cls,
        title: str,
        requested_role: str,
    ) -> bool:
        normalized_title = cls._normalize(title)
        normalized_role = cls._normalize(requested_role)

        if not normalized_role:
            return False

        return normalized_role in normalized_title

    # ----------------------------------------------------------
    # Role aliases
    # ----------------------------------------------------------

    @staticmethod
    def _aliases(role: str) -> set[str]:
        normalized = RoleQualifier._normalize(role)

        aliases: dict[str, set[str]] = {
            "program manager": {
                "program manager",
                "program management",
            },
            "technical program manager": {
                "technical program manager",
                "technical program management",
                "tpm",
            },
            "project manager": {
                "project manager",
                "project management",
            },
            "delivery manager": {
                "delivery manager",
                "delivery management",
            },
            "pmo": {
                "pmo",
                "project management office",
            },
            "pmo analyst": {
                "pmo analyst",
                "project management office analyst",
            },
            "transformation manager": {
                "transformation manager",
                "transformation management",
            },
            "implementation manager": {
                "implementation manager",
                "implementation management",
            },
            "operations manager": {
                "operations manager",
                "operations management",
            },
        }

        return aliases.get(
            normalized,
            {normalized},
        )

    # ----------------------------------------------------------
    # Qualification
    # ----------------------------------------------------------

    def qualify(
        self,
        title: str,
        requested_roles: Iterable[str],
    ) -> RoleQualificationResult:

        if not title:
            return RoleQualificationResult(
                qualified=False,
                reason="Job title is empty.",
            )

        roles = [
            role.strip()
            for role in requested_roles
            if role and role.strip()
        ]

        if not roles:
            return RoleQualificationResult(
                qualified=False,
                reason="No target roles were provided.",
            )

        normalized_title = self._normalize(title)

        # ------------------------------------------------------
        # Pass 1: explicit phrase / alias matching
        # ------------------------------------------------------

        for role in roles:

            aliases = self._aliases(role)

            for alias in aliases:

                if alias in normalized_title:

                    return RoleQualificationResult(
                        qualified=True,
                        matched_role=role,
                        reason=(
                            f"Title matched requested role "
                            f"'{role}' via '{alias}'."
                        ),
                    )

        # ------------------------------------------------------
        # Pass 2: controlled token overlap
        #
        # This catches variants such as:
        #
        # Senior Technical Program Manager
        # Global Program Management Lead
        #
        # while avoiding broad matches such as:
        #
        # Data Analyst
        # Risk Operations Analyst
        # Copywriter
        # ------------------------------------------------------

        title_tokens = self._tokens(title)

        for role in roles:

            normalized_role = self._normalize(role)

            role_tokens = self._tokens(normalized_role)

            if not role_tokens:
                continue

            # Generic words are not sufficient evidence for a role.
            generic_tokens = {
                "manager",
                "management",
                "senior",
                "lead",
                "director",
                "analyst",
                "associate",
                "specialist",
                "operations",
                "business",
            }

            meaningful_role_tokens = (
                role_tokens - generic_tokens
            )

            if not meaningful_role_tokens:
                continue

            matched_tokens = (
                meaningful_role_tokens & title_tokens
            )

            if matched_tokens == meaningful_role_tokens:

                return RoleQualificationResult(
                    qualified=True,
                    matched_role=role,
                    reason=(
                        f"Title matched role-specific tokens "
                        f"for '{role}'."
                    ),
                )

        return RoleQualificationResult(
            qualified=False,
            reason=(
                f"Role '{title}' is outside the requested "
                f"role families."
            ),
        )