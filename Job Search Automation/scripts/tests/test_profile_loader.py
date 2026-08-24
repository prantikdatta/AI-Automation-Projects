from job_search_automation.profile.loader import (
    ResumeProfileLoader,
)


profile = ResumeProfileLoader.load()

print(profile.name)

print(profile.experience_years)

print(profile.skills[:10])

print(profile.preferred_roles)

print(profile.preferred_locations)