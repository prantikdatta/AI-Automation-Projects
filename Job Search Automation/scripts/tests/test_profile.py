from job_search_automation.profile.loader import (
    ResumeProfileLoader,
)

profile = ResumeProfileLoader.load()

print(profile)