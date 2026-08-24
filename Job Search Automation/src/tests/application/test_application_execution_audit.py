from __future__ import annotations

from job_search_automation.application.execution_audit import (
    ApplicationExecutionAudit,
    ApplicationExecutionAuditError,
)


def test_audit_starts_not_started() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    assert audit.status == "NOT_STARTED"
    assert audit.job_id == "job-001"


def test_audit_transitions_to_ready() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready(
        message="Execution ready.",
        metadata={
            "channel": "fake",
        },
    )

    assert audit.status == "READY"
    assert audit.message == "Execution ready."
    assert audit.metadata["channel"] == "fake"


def test_audit_transitions_to_submitted() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready()

    audit.mark_submitted(
        message="Application submitted.",
        metadata={
            "executor": "fake",
        },
    )

    assert audit.status == "SUBMITTED"
    assert audit.message == "Application submitted."
    assert audit.metadata["executor"] == "fake"


def test_audit_transitions_to_failed() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready()

    audit.mark_failed(
        message="External executor failed.",
        metadata={
            "error_type": "RuntimeError",
        },
    )

    assert audit.status == "FAILED"
    assert audit.message == "External executor failed."
    assert audit.metadata["error_type"] == "RuntimeError"


def test_failed_execution_can_be_recorded_before_ready() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_failed(
        message="Pre-execution validation failed."
    )

    assert audit.status == "FAILED"


def test_invalid_transition_is_rejected() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready()
    audit.mark_submitted()

    try:
        audit.mark_ready()
    except ApplicationExecutionAuditError as exc:
        assert "SUBMITTED" in str(exc)
        assert "READY" in str(exc)
    else:
        raise AssertionError(
            "Expected ApplicationExecutionAuditError."
        )


def test_terminal_submitted_state_cannot_be_failed() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready()
    audit.mark_submitted()

    try:
        audit.mark_failed(
            message="Late failure."
        )
    except ApplicationExecutionAuditError:
        pass
    else:
        raise AssertionError(
            "Expected terminal SUBMITTED state to reject failure."
        )


def test_to_dict_returns_serializable_audit() -> None:
    audit = ApplicationExecutionAudit(
        job_id="job-001"
    )

    audit.mark_ready(
        metadata={
            "executor": "fake",
        }
    )

    payload = audit.to_dict()

    assert payload["job_id"] == "job-001"
    assert payload["status"] == "READY"
    assert isinstance(
        payload["created_at"],
        str,
    )
    assert isinstance(
        payload["updated_at"],
        str,
    )
    assert payload["metadata"]["executor"] == "fake"