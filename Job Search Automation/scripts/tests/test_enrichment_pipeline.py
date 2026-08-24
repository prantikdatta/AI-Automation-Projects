from job_search_automation.models.job import Job
from job_search_automation.enrichment import EnrichmentPipeline


job = Job(
    searched_role="Analytics",
    title="Senior Strategy Analytics Business Partner",
    company="Stripe",
    location="Bengaluru",
    description="""
    Build analytics solutions using Python,
    SQL, Power BI and Databricks.
    Partner with finance and product teams.
    """,
    job_url="test",
    source="test",
    provider="test",
)


job = EnrichmentPipeline.process(job)


print("TITLE:", job.title)
print("SKILLS:", job.skills)
print("BUCKET:", job.job_bucket)
print("SENIORITY:", job.seniority)
print("SCORE:", job.overall_score)
print("RECOMMENDATION:", job.recommendation)
print("PRIORITY:", job.apply_priority)
print("EXPLANATION:", job.overall_explanation)