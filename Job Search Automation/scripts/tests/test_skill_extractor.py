from job_search_automation.models.job import Job
from job_search_automation.enrichment import SkillExtractor


job = Job(
    searched_role="Analytics Engineer",
    title="Strategy Analytics Manager",
    company="Stripe",
    location="Bangalore",
    description="""
    Required skills:
    Python, SQL, Power BI, Databricks,
    data analysis and business intelligence.
    """,
    job_url="test",
    source="test",
    provider="test",
)


job = SkillExtractor.extract(job)

print(job.skills)