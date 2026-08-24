from job_search_automation.models.job import Job
from job_search_automation.enrichment import (
    SkillExtractor,
    RoleClassifier,
    JobScorer,
)


job = Job(
    searched_role="Analytics",
    title="Senior Strategy Analytics Business Partner",
    company="Stripe",
    location="Bengaluru",
    description="""
    Python SQL Power BI Databricks.
    Build analytics solutions for finance teams.
    """,
    job_url="test",
    source="test",
    provider="test",
)


job = SkillExtractor.extract(job)

job = RoleClassifier.classify(job)

job = JobScorer.score(job)


print("Skills:", job.skills)
print("Bucket:", job.job_bucket)
print("Seniority:", job.seniority)
print("Score:", job.overall_score)
print("Recommendation:", job.recommendation)
print("Priority:", job.apply_priority)
print("Reason:", job.overall_explanation)