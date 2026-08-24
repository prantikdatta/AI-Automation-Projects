from __future__ import annotations

from job_search_automation.intelligence.qualification import (
    CandidateQualifier,
    LocationQualifier,
    RoleQualifier,
)
from job_search_automation.models.job import Job
from job_search_automation.models.request import SearchRequest


def make_job(
    title: str,
    location: str,
) -> Job:
    return Job(
        title=title,
        company="Test Company",
        location=location,
        description="Test description",
        job_url="https://example.com/job",
        source="test",

        # --------------------------------------------------
        # Canonical Job Contract
        # --------------------------------------------------

        searched_role=title,
        provider="test",
    )


def make_request() -> SearchRequest:

    return SearchRequest(
        searched_role="Program Management",
        keywords=[],
        locations=[
            "Mumbai",
            "Bengaluru",
            "Hyderabad",
            "Remote India",
        ],
        bucket="Program Management",
        roles=[
            "Program Manager",
            "Technical Program Manager",
            "Project Manager",
            "Delivery Manager",
            "PMO",
            "PMO Analyst",
            "Transformation Manager",
            "Implementation Manager",
            "Operations Manager",
        ],
        priority=3,
    )


def test_program_manager_matches():

    result = RoleQualifier().qualify(
        "Senior Program Manager",
        make_request().roles,
    )

    assert result.qualified is True


def test_data_analyst_does_not_match_program_management():

    result = RoleQualifier().qualify(
        "Data Analyst",
        make_request().roles,
    )

    assert result.qualified is False


def test_project_manager_matches():

    result = RoleQualifier().qualify(
        "Senior Project Manager",
        make_request().roles,
    )

    assert result.qualified is True


def test_bangalore_matches_bengaluru():

    result = LocationQualifier().qualify(
        job_location="Bangalore",
        requested_locations=["Bengaluru"],
    )

    assert result.qualified is True


def test_new_york_is_rejected():

    result = LocationQualifier().qualify(
        job_location="New York",
        requested_locations=["Mumbai"],
    )

    assert result.qualified is False


def test_remote_india_matches_remote():

    result = LocationQualifier().qualify(
        job_location="Remote",
        requested_locations=["Remote India"],
    )

    assert result.qualified is True


def test_candidate_qualifier_requires_both_role_and_location():

    request = make_request()

    qualifier = CandidateQualifier()

    valid = qualifier.qualify(
        job=make_job(
            "Senior Program Manager",
            "Mumbai",
        ),
        request=request,
    )

    assert valid.qualified is True

    invalid_role = qualifier.qualify(
        job=make_job(
            "Data Analyst",
            "Mumbai",
        ),
        request=request,
    )

    assert invalid_role.qualified is False

    invalid_location = qualifier.qualify(
        job=make_job(
            "Senior Program Manager",
            "New York",
        ),
        request=request,
    )

    assert invalid_location.qualified is False