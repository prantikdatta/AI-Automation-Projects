# Provider Guide

## 1. Purpose

The provider layer is responsible for collecting job opportunities from external job sources and converting them into the application's canonical `Job` model.

The provider layer isolates external-source differences from the rest of the application.

The core boundary is:

```text
External Job Source
        |
        v
Provider
        |
        v
Provider Client
        |
        v
Raw Provider Payload
        |
        v
Provider Normalizer
        |
        v
CanonicalMapper
        |
        v
Canonical Job
        |
        v
SearchResponse
```

Downstream pipeline stages consume canonical `Job` objects rather than provider-specific payload structures.

---

## 2. Provider Contract

The common provider abstraction is defined in:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\base.py
```

The canonical provider interaction is:

```text
SearchRequest
      |
      v
Provider.search()
      |
      v
SearchResponse
      |
      +--> provider
      +--> jobs
      +--> total_found
      +--> total_returned
      +--> success
      +--> message
```

The provider returns:

```text
list[Job]
```

inside the `SearchResponse`.

Provider-specific response structures should not propagate into the core pipeline. The canonical `Job` model is the downstream contract.

---

## 3. Provider Responsibilities

A provider is responsible for:

* receiving a canonical `SearchRequest`
* constructing provider-specific requests
* calling the external source through its client
* retrieving raw job data
* handling provider-specific response structures
* normalizing provider fields
* converting normalized data into canonical `Job` objects
* returning a `SearchResponse`
* isolating provider-specific failures where possible

A provider is not responsible for:

* global deduplication
* final freshness filtering
* candidate/job scoring
* ranking the complete provider pool
* final selection
* Google Sheets export
* application execution

The separation ensures that adding or changing a provider does not require rewriting the business-intelligence layer.

---

# 4. Current Provider Landscape

The repository contains API-based and ATS-based provider implementations.

## API / Job-board providers

The provider implementation set includes:

```text
RapidAPI / JSearch
Jooble
Adzuna
Remotive
Apify
Google Jobs
JobSpy
```

Relevant provider files include:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\rapidapi_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\jooble_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\adzuna_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\remotive_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\apify_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\google_jobs_provider.py
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\jobspy_provider.py
```

The repository architecture documentation also identifies these sources as part of the provider layer.

## ATS providers

The provider layer also includes ATS integrations for:

```text
Greenhouse
Lever
Ashby
Workday
SmartRecruiters
BambooHR
```

The corresponding provider implementations are part of the provider/ATS abstraction.

The repository also contains a separate ATS orchestration structure under:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\ats\
```

The ATS layer includes registry, factory, filtering and orchestration concepts.

---

# 5. Provider Registry

Provider discovery is centralized through the provider registry.

Relevant files:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\provider_registry.py

F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\ats_registry.py
```

Supporting provider infrastructure includes:

```text
provider_executor.py
provider_health.py
provider_metrics.py
provider_manager.py
provider_router.py
provider_stats.py
provider_cache.py
metadata.py
capabilities.py
```

These components allow the orchestration layer to work with providers through common interfaces instead of embedding provider-specific implementation details.

---

# 6. Provider Manager and Execution

The provider manager coordinates provider execution.

Conceptually:

```text
SearchRequest
      |
      v
Provider Manager / Orchestrator
      |
      +----> RapidAPI
      +----> Jooble
      +----> Adzuna
      +----> Remotive
      +----> Apify
      +----> Google Jobs
      +----> ATS providers
      |
      v
Provider Responses
      |
      v
Canonical Jobs
```

The `SearchOrchestrator` is responsible for collecting jobs from the configured sources.

The `SearchPipeline` does not directly implement each provider's API logic. Instead, it delegates collection to the search orchestration layer. The pipeline source explicitly initializes a `SearchOrchestrator` and calls it to collect jobs.

---

# 7. RapidAPI / JSearch

Implementation:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\rapidapi_provider.py
```

Client:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\clients\rapidapi_client.py
```

Normalizer:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\normalizers\rapidapi.py
```

The flow is:

```text
SearchRequest
      |
      v
RapidAPIProvider
      |
      v
RapidAPIClient
      |
      v
JSearch
      |
      v
RapidAPINormalizer
      |
      v
CanonicalMapper
      |
      v
Job
```

The current provider implementation uses:

```text
query = request.searched_role
page = 1
num_pages = 5
```

and then normalizes each returned job before mapping it to the canonical model.

Skill extraction is also applied to the normalized description before the job is mapped into the canonical model.

---

# 8. Apify

Implementation:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\apify_provider.py
```

Client:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\clients\apify_client.py
```

Normalizer:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\normalizers\apify.py
```

The flow is:

```text
SearchRequest
      |
      v
ApifyProvider
      |
      v
ApifyClient
      |
      v
Apify Actor
      |
      v
ApifyNormalizer
      |
      v
CanonicalMapper
      |
      v
Job
```

The current implementation passes:

```text
query = request.searched_role
location = India
max_items = request.limit
```

and maps the normalized result to the canonical `Job` model.

## Apify URL rule

The Apify integration must distinguish between a valid direct job/application URL and an unusable search or placeholder URL.

The normalizer must not manufacture a direct application URL when the provider has not supplied one.

Therefore:

```text
Valid direct job URL
        |
        v
Accept
```

while:

```text
Google Jobs search URL
        |
        v
Do not treat as application URL
```

and:

```text
Placeholder URL
        |
        v
Do not treat as application URL
```

This protects downstream application preparation from false or unusable links.

---

# 9. Google Jobs

Implementation:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\google_jobs_provider.py
```

Client:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\clients\google_jobs_client.py
```

The implementation uses SerpAPI's Google Jobs search engine.

The provider receives keywords from `SearchRequest` and converts the returned Google Jobs records into canonical `Job` objects.

The provider maps fields such as:

```text
title
company
location
description
job_url
employment_type
remote
work_mode
```

into the canonical model.

---

# 10. ATS Provider Architecture

ATS providers are treated as a distinct class of source because they generally retrieve employer-specific job inventories rather than a broad job-board search result.

The shared ATS abstraction is:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\ats_provider.py
```

The base ATS provider is responsible for:

* downloading available jobs
* caching provider results
* applying local relevance filtering
* returning canonical `SearchResponse` objects

The repository implementation uses:

```text
ProviderCache
RoleMatcher
ProviderMetadata
ProviderCapabilities
```

within this abstraction.

Conceptually:

```text
ATS Provider
     |
     v
Fetch Jobs
     |
     v
Cache
     |
     v
Role Relevance Filtering
     |
     v
SearchResponse
```

---

# 11. ATS Implementations

The current provider implementation set includes:

```text
Greenhouse
Lever
Ashby
Workday
SmartRecruiters
BambooHR
```

The architecture documentation identifies these as ATS sources.

An ATS provider should expose jobs through the same canonical provider contract used by other providers.

---

# 12. ATS Filtering

ATS search results are filtered for relevance before being returned to the broader pipeline.

Typical relevance dimensions include:

```text
role
keywords
location
remote eligibility
analytics relevance
business intelligence relevance
```

The repository's ATS orchestration configuration includes target locations such as:

```text
Mumbai
Bangalore
Bengaluru
Hyderabad
India
Remote
```

and keywords such as:

```text
data analyst
business analyst
analytics
business intelligence
product analyst
BI
```

This filtering happens at the provider/ATS boundary rather than inside the global scoring engine.

---

# 13. Normalization

Normalization is the critical boundary between external providers and the core pipeline.

The general flow is:

```text
External Payload
      |
      v
Provider Normalizer
      |
      v
Normalized Job Representation
      |
      v
CanonicalMapper
      |
      v
Job
```

The normalizer handles provider-specific differences such as:

```text
field names
dates
locations
URLs
salary information
employment type
work mode
descriptions
```

The `CanonicalMapper` then constructs the canonical `Job`.

Downstream stages should consume the canonical model rather than provider-specific JSON.

---

# 14. Canonical Job Boundary

Once a provider has produced:

```text
Job
```

the provider-specific contract has ended.

The downstream system should not contain code such as:

```text
if provider == "RapidAPI":
    ...
```

for core scoring or selection logic.

Instead:

```text
Provider
   |
   v
Canonical Job
   |
   v
Core Pipeline
```

This allows providers to evolve independently.

---

# 15. Provider Health and Failure Isolation

Provider failure is operationally different from a bad candidate/job score.

Possible provider outcomes include:

```text
SUCCESS
EMPTY
DEGRADED
FAILED
UNAVAILABLE
```

For example:

```text
RapidAPI
    |
    +--> HTTP 429
    |
    +--> DEGRADED
```

while:

```text
Greenhouse
    |
    +--> SUCCESS
```

The provider orchestration layer should preserve valid results from healthy providers whenever possible.

A provider-specific failure should not automatically invalidate the entire search.

---

# 16. Provider Cache

Provider caching is used in the ATS architecture to reduce repeated external requests.

The cache boundary is:

```text
ATS Provider
      |
      v
ProviderCache.has()
      |
      +---- cached --> use cached jobs
      |
      +---- miss ----> fetch jobs
                          |
                          v
                    ProviderCache.set()
```

The cached result is then filtered against the current `SearchRequest`.

---

# 17. Provider Metadata and Capabilities

Provider metadata is represented through:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\metadata.py
```

Capabilities are represented through:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\providers\capabilities.py
```

These abstractions allow the orchestration layer to reason about provider characteristics without coupling downstream logic to a particular API.

---

# 18. Adding a New Provider

A new provider should be implemented in this order:

```text
1. Provider class
        |
2. Provider client
        |
3. Provider normalizer
        |
4. CanonicalMapper integration
        |
5. Registry/configuration
        |
6. Unit tests
        |
7. Live smoke validation
        |
8. Provider health/error handling
```

The provider should then return:

```text
SearchResponse
```

containing canonical `Job` objects.

A new provider should not require modifications to:

```text
ResumeMatcher
FinalScoreCalculator
FinalSelectionEngine
GoogleSheetsService
```

unless the new provider introduces a genuinely new system-level capability.

---

# 19. Provider Testing

Provider tests belong under:

```text
F:\CodeBasics\VS CODE\job-search-automation\tests\
```

Live validation scripts belong under:

```text
F:\CodeBasics\VS CODE\job-search-automation\scripts\validation\
```

Provider validation should check:

```text
request construction
response handling
normalization
canonical mapping
required fields
URL validity
empty responses
provider errors
rate limits
```

The controlled provider smoke test specifically validates:

```text
Provider response
      |
      v
Existing normalizer
      |
      v
Existing CanonicalMapper
      |
      v
Canonical Job
```

and does not run the complete production pipeline or application execution workflow.

---

# 20. Credential Handling

Provider credentials must not be hard-coded in provider source files.

Credentials belong in the configured environment/secrets mechanism.

The repository should contain:

```text
.env.example
```

for configuration guidance, while the real:

```text
.env
```

must remain outside Git.

Provider logs and validation output must also avoid printing full credentials.

---

# 21. Provider Boundary Summary

The complete provider boundary is:

```text
                 EXTERNAL SOURCES
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
     API Jobs        ATS Systems      Google Jobs
        |               |                |
        +---------------+----------------+
                        |
                        v
                   Provider Layer
                        |
                        v
                  Provider Client
                        |
                        v
                 Raw Provider Data
                        |
                        v
                   Normalizer
                        |
                        v
                  CanonicalMapper
                        |
                        v
                       Job
                        |
                        v
                  SearchResponse
                        |
                        v
               Core Search Pipeline
```

The provider layer owns **source acquisition and source-specific normalization**.

The core pipeline owns **deduplication, freshness, enrichment, matching, scoring, ranking, selection, and export**.

That separation is the central design principle of the provider architecture.
