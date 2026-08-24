from job_search_automation.models.job import Job
from job_search_automation.enrichment import RoleClassifier


job = Job(
    searched_role="Analytics",
    title="Senior Strategy Analytics Business Partner",
    company="Stripe",
    location="Bangalore",
    description="""
    Work with product and finance teams.
    Build analytics solutions using SQL and BI tools.
    """,
    job_url="test",
    source="test",
    provider="test",
)


job = RoleClassifier.classify(job)

print(job.job_bucket)
print(job.seniority)