# Sequence Diagram

## 1. Purpose

This document describes the runtime sequence of the Job Search Automation system from scheduling through provider collection, normalization, enrichment, candidate matching, scoring, final selection, and Google Sheets export.

The production application follows this overall flow:

```text
n8n
  |
  v
FastAPI
  |
  v
SearchPipeline
  |
  v
SearchOrchestrator
  |
  v
Provider Layer
  |
  v
Canonical Jobs
  |
  v
Deduplication
  |
  v
Freshness Filtering
  |
  v
Enrichment
  |
  v
Resume Matching
  |
  v
Ranking
  |
  v
Final Selection
  |
  v
Google Sheets
```

---

## 2. Production End-to-End Sequence

```mermaid
sequenceDiagram

    participant N8N as n8n
    participant API as FastAPI
    participant PIPE as SearchPipeline
    participant ORCH as SearchOrchestrator
    participant PROVIDERS as Provider Layer
    participant DEDUP as Deduplication
    participant FRESH as Freshness Filter
    participant ENR as EnrichmentPipeline
    participant MATCH as ResumeMatcher
    participant SELECT as FinalSelectionEngine
    participant SHEETS as Google Sheets

    N8N->>API: POST /jobs/search

    API->>PIPE: Execute pipeline

    PIPE->>ORCH: collect_jobs()

    ORCH->>PROVIDERS: Search configured providers

    PROVIDERS-->>ORCH: SearchResponse objects

    ORCH-->>PIPE: Canonical Job objects

    PIPE->>DEDUP: deduplicate_jobs()

    DEDUP-->>PIPE: Deduplicated jobs

    PIPE->>FRESH: apply_freshness_filter()

    FRESH-->>PIPE: Fresh jobs

    loop Each surviving job
        PIPE->>ENR: process(job)
        ENR-->>PIPE: Enriched job

        PIPE->>MATCH: evaluate(job)
        MATCH-->>PIPE: ResumeMatchResult
    end

    PIPE->>PIPE: Rank by overall_score

    PIPE->>SELECT: Evaluate final selection

    SELECT-->>PIPE: Selected / rejected jobs

    PIPE->>SHEETS: Export selected jobs

    SHEETS-->>PIPE: Export status

    PIPE-->>API: SearchResponse

    API-->>N8N: HTTP response
```

---

## 3. Scheduling and API Boundary

n8n is responsible for scheduling and triggering the Python application.

Python owns the job-search business logic.

```text
n8n
 |
 | Scheduled trigger
 v
POST /jobs/search
 |
 v
FastAPI
 |
 v
SearchPipeline
```

The local API endpoint is:

```text
http://127.0.0.1:8000/jobs/search
```

The health endpoint is:

```text
http://127.0.0.1:8000/health
```

The responsibility split is:

```text
n8n
 |
 +--> Scheduling
 +--> Workflow triggering
 +--> HTTP invocation
 +--> Workflow orchestration

Python Application
 |
 +--> Provider collection
 +--> Normalization
 +--> Deduplication
 +--> Freshness filtering
 +--> Enrichment
 +--> Resume matching
 +--> Scoring
 +--> Ranking
 +--> Final selection
 +--> Google Sheets export
```

n8n should not duplicate the Python application's business logic.

---

## 4. Provider Collection Sequence

The `SearchPipeline` delegates job collection to `SearchOrchestrator`.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant ORCH as SearchOrchestrator
    participant PROVIDERS as Provider Layer

    PIPE->>ORCH: collect_jobs()

    ORCH->>PROVIDERS: Execute configured providers

    PROVIDERS-->>ORCH: SearchResponse objects

    ORCH->>ORCH: Aggregate provider results

    ORCH-->>PIPE: Canonical Job objects
```

The provider layer can include:

```text
RapidAPI / JSearch
Jooble
Adzuna
Remotive
Apify
Google Jobs
JobSpy
Greenhouse
Lever
Ashby
Workday
SmartRecruiters
BambooHR
```

---

## 5. Single Provider Sequence

Every provider follows the same conceptual boundary:

```mermaid
sequenceDiagram

    participant ORCH as SearchOrchestrator
    participant PROVIDER as Provider
    participant CLIENT as Provider Client
    participant SOURCE as External Source
    participant NORM as Provider Normalizer
    participant MAP as CanonicalMapper

    ORCH->>PROVIDER: search(SearchRequest)

    PROVIDER->>CLIENT: Build provider request

    CLIENT->>SOURCE: External request

    SOURCE-->>CLIENT: Raw payload

    CLIENT-->>PROVIDER: Raw provider data

    PROVIDER->>NORM: Normalize payload

    NORM-->>PROVIDER: Normalized job

    PROVIDER->>MAP: Convert to Job

    MAP-->>PROVIDER: Canonical Job

    PROVIDER-->>ORCH: SearchResponse
```

The provider boundary is therefore:

```text
External Source
      |
      v
Provider Client
      |
      v
Raw Payload
      |
      v
Normalizer
      |
      v
CanonicalMapper
      |
      v
Job
```

Downstream stages should consume `Job`, not provider-specific JSON.

---

## 6. RapidAPI Sequence

```mermaid
sequenceDiagram

    participant ORCH as SearchOrchestrator
    participant RAPID as RapidAPIProvider
    participant CLIENT as RapidAPIClient
    participant JSEARCH as JSearch
    participant NORM as RapidAPINormalizer
    participant MAP as CanonicalMapper

    ORCH->>RAPID: search(SearchRequest)

    RAPID->>CLIENT: search_jobs(query, page, num_pages)

    CLIENT->>JSEARCH: HTTP request

    JSEARCH-->>CLIENT: JSON response

    CLIENT-->>RAPID: Raw payload

    loop Each returned job
        RAPID->>NORM: normalize(raw_job)
        NORM-->>RAPID: Normalized job

        RAPID->>RAPID: Extract skills

        RAPID->>MAP: to_job(normalized)
        MAP-->>RAPID: Canonical Job
    end

    RAPID-->>ORCH: SearchResponse
```

---

## 7. Apify Sequence

```mermaid
sequenceDiagram

    participant ORCH as SearchOrchestrator
    participant APIFY as ApifyProvider
    participant CLIENT as ApifyClient
    participant ACTOR as Apify Actor
    participant NORM as ApifyNormalizer
    participant MAP as CanonicalMapper

    ORCH->>APIFY: search(SearchRequest)

    APIFY->>CLIENT: search_jobs(query, location, max_items)

    CLIENT->>ACTOR: Execute actor / retrieve results

    ACTOR-->>CLIENT: Raw jobs

    CLIENT-->>APIFY: Raw payload

    loop Each returned job
        APIFY->>NORM: normalize(raw)
        NORM-->>APIFY: Normalized job

        APIFY->>MAP: to_job(normalized)
        MAP-->>APIFY: Canonical Job
    end

    APIFY-->>ORCH: SearchResponse
```

### Apify URL validation

The Apify normalizer must distinguish between a real direct job/application URL and an unusable URL.

```text
Valid direct job URL
        |
        v
Accept
```

```text
Google Jobs search URL
        |
        v
Reject as application URL
```

```text
Placeholder URL
        |
        v
Reject as application URL
```

The system must not manufacture a direct application URL when the provider did not supply a valid one.

---

## 8. ATS Provider Sequence

ATS providers retrieve jobs from employer applicant-tracking systems.

```mermaid
sequenceDiagram

    participant ORCH as SearchOrchestrator
    participant ATS as ATS Provider
    participant CACHE as ProviderCache
    participant SOURCE as Employer ATS
    participant FILTER as RoleMatcher

    ORCH->>ATS: search(SearchRequest)

    ATS->>CACHE: Check cached provider jobs

    alt Cached data available
        CACHE-->>ATS: Cached jobs
    else Cache miss
        ATS->>SOURCE: Fetch jobs
        SOURCE-->>ATS: Employer jobs
        ATS->>CACHE: Store jobs
    end

    ATS->>FILTER: Filter relevant jobs

    FILTER-->>ATS: Relevant jobs

    ATS-->>ORCH: SearchResponse
```

ATS filtering may use:

```text
role
keywords
location
remote eligibility
analytics relevance
business intelligence relevance
```

---

## 9. Provider Failure Isolation

A provider failure should not automatically terminate the entire search.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant RAPID as RapidAPI
    participant APIFY as Apify
    participant ATS as ATS Providers

    PIPE->>RAPID: Search
    RAPID-->>PIPE: Provider failure / degraded response

    PIPE->>APIFY: Continue provider execution
    APIFY-->>PIPE: Valid jobs

    PIPE->>ATS: Continue provider execution
    ATS-->>PIPE: Valid jobs

    PIPE->>PIPE: Aggregate available jobs
```

Example:

```text
RapidAPI
    -> DEGRADED

Apify
    -> SUCCESS

ATS Providers
    -> SUCCESS
```

The orchestration layer should preserve successful results from available providers wherever safe.

---

## 10. Deduplication Sequence

After provider collection, duplicate opportunities are removed.

```mermaid
sequenceDiagram

    participant ORCH as SearchOrchestrator
    participant PIPE as SearchPipeline
    participant DEDUP as Deduplication

    ORCH-->>PIPE: Collected Job objects

    PIPE->>DEDUP: deduplicate_jobs(jobs)

    DEDUP->>DEDUP: Normalize job identity

    DEDUP->>DEDUP: Identify duplicates

    DEDUP-->>PIPE: Unique jobs
```

Deduplication occurs before expensive enrichment and intelligence processing.

---

## 11. Freshness Sequence

The freshness filter removes stale job postings.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant FRESH as Freshness Filter

    PIPE->>FRESH: apply_freshness_filter(jobs)

    FRESH->>FRESH: Evaluate posting dates

    FRESH->>FRESH: Remove stale jobs

    FRESH-->>PIPE: Fresh jobs
```

The documented production rule removes jobs outside the configured freshness window.

---

## 12. Enrichment Sequence

The enrichment pipeline adds deterministic job metadata before candidate matching.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant ENR as EnrichmentPipeline
    participant SKILL as SkillExtractor
    participant ROLE as RoleClassifier

    PIPE->>ENR: process(job)

    ENR->>SKILL: Extract skills
    SKILL-->>ENR: Job with skills

    ENR->>ROLE: Classify role
    ROLE-->>ENR: Enriched Job

    ENR-->>PIPE: Enriched Job
```

The enrichment stage includes deterministic operations such as:

```text
Skill extraction
Role classification
Job-family classification
Seniority classification
```

---

## 13. Resume Matching Sequence

The `ResumeMatcher` evaluates each surviving job against the candidate profile.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant MATCH as ResumeMatcher
    participant SKILL as SkillMatcher
    participant EXP as ExperienceMatcher
    participant CAREER as CareerProgressionMatcher
    participant LOC as LocationMatcher
    participant COMPANY as CompanyScorer
    participant FRESH as FreshnessScorer

    PIPE->>MATCH: evaluate(job)

    MATCH->>SKILL: Match skills
    SKILL-->>MATCH: Skill result

    MATCH->>EXP: Match experience
    EXP-->>MATCH: Experience result

    MATCH->>LOC: Match location / remote
    LOC-->>MATCH: Location result

    MATCH->>CAREER: Match career progression
    CAREER-->>MATCH: Career result

    MATCH->>COMPANY: Score company
    COMPANY-->>MATCH: Company result

    MATCH->>FRESH: Score freshness
    FRESH-->>MATCH: Freshness result

    MATCH-->>PIPE: Component scoring results
```

---

## 14. Weighted Score Calculation

The final deterministic score is calculated from the six scoring components:

```text
Skill Match
Experience Match
Career Progression
Location Match
Company Score
Freshness Score
```

The current weights are:

```text
Skills              30%
Experience          20%
Career progression  15%
Location            10%
Company             10%
Freshness           15%
                    ----
                    100%
```

The scoring sequence is:

```mermaid
sequenceDiagram

    participant MATCH as ResumeMatcher
    participant SCORE as FinalScoreCalculator

    MATCH->>SCORE: skill_result
    MATCH->>SCORE: experience_result
    MATCH->>SCORE: career_result
    MATCH->>SCORE: location_result
    MATCH->>SCORE: company_result
    MATCH->>SCORE: freshness_result

    SCORE->>SCORE: Apply configured weights

    SCORE-->>MATCH: overall_score
```

The deterministic score remains the authoritative job/candidate score.

---

## 15. Gemini Enrichment Sequence

Gemini enrichment is supplementary to deterministic scoring.

```mermaid
sequenceDiagram

    participant MATCH as ResumeMatcher
    participant SCORE as Deterministic Score
    participant GEMINI as GeminiClient

    MATCH->>SCORE: Calculate deterministic score

    SCORE-->>MATCH: overall_score

    alt Job qualifies for Gemini enrichment
        MATCH->>GEMINI: Analyze / enrich job
        GEMINI-->>MATCH: AI enrichment
    else Not selected for enrichment
        MATCH->>MATCH: Keep deterministic result
    end
```

The deterministic score is not replaced by Gemini output.

Gemini can provide additional information such as:

```text
job analysis
resume tailoring
cover letter generation
interview preparation
```

---

## 16. Ranking Sequence

After evaluation, jobs are ranked by the deterministic overall score.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline

    PIPE->>PIPE: Collect evaluated jobs

    PIPE->>PIPE: Sort by overall_score DESC

    PIPE-->>PIPE: Ranked jobs
```

The ranking stage therefore operates after enrichment and resume matching.

---

## 17. Final Selection Sequence

`FinalSelectionEngine` is responsible for deciding which evaluated jobs belong in the final application queue.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant SELECT as FinalSelectionEngine

    PIPE->>SELECT: Ranked jobs

    SELECT->>SELECT: Evaluate eligibility

    SELECT->>SELECT: Evaluate role / location rules

    SELECT->>SELECT: Evaluate score thresholds

    SELECT->>SELECT: Assign bucket

    SELECT->>SELECT: Assign priority

    SELECT-->>PIPE: Selected / rejected jobs
```

The final decision includes fields such as:

```text
final_selection_eligible
final_selection_bucket
final_selection_reason
final_selection_priority
```

---

## 18. Application Queue Boundary

The search pipeline prepares the final application queue.

```text
Ranked Jobs
     |
     v
FinalSelectionEngine
     |
     +------------------+
     |                  |
     v                  v
Eligible             Rejected
     |
     v
Application Queue
```

The application execution layer remains downstream of discovery and scoring.

The system should therefore distinguish:

```text
Job discovery
```

from:

```text
Application execution
```

---

## 19. Google Sheets Export Sequence

Selected jobs are mapped to rows and exported to Google Sheets.

```mermaid
sequenceDiagram

    participant PIPE as SearchPipeline
    participant SELECT as FinalSelectionEngine
    participant MAP as Google Sheets Mapper
    participant SHEETS as GoogleSheetsService
    participant WORKSHEET as Google Sheets

    PIPE->>SELECT: Final evaluated jobs

    SELECT-->>PIPE: Selected jobs

    PIPE->>MAP: job_to_row(selected_jobs)

    MAP-->>PIPE: Sheet rows

    PIPE->>SHEETS: Export rows

    SHEETS->>WORKSHEET: Append rows

    WORKSHEET-->>SHEETS: Write status

    SHEETS-->>PIPE: Export complete
```

Google Sheets acts as the current reporting and tracking destination for the selected jobs.

---

## 20. Complete Production Sequence

```mermaid
sequenceDiagram

    participant N8N as n8n
    participant API as FastAPI
    participant PIPE as SearchPipeline
    participant ORCH as SearchOrchestrator
    participant PROVIDERS as Providers
    participant DEDUP as Deduplication
    participant FRESH as Freshness
    participant ENR as Enrichment
    participant MATCH as ResumeMatcher
    participant SCORE as FinalScoreCalculator
    participant GEMINI as Gemini
    participant SELECT as FinalSelectionEngine
    participant SHEETS as Google Sheets

    N8N->>API: POST /jobs/search

    API->>PIPE: run()

    PIPE->>ORCH: collect_jobs()

    ORCH->>PROVIDERS: Search configured providers

    PROVIDERS-->>ORCH: SearchResponse objects

    ORCH-->>PIPE: Canonical Jobs

    PIPE->>DEDUP: Deduplicate

    DEDUP-->>PIPE: Unique Jobs

    PIPE->>FRESH: Freshness filtering

    FRESH-->>PIPE: Fresh Jobs

    loop Each surviving job

        PIPE->>ENR: Enrich job
        ENR-->>PIPE: Enriched Job

        PIPE->>MATCH: Evaluate job

        MATCH->>SCORE: Calculate weighted score
        SCORE-->>MATCH: overall_score

        opt Gemini enrichment
            MATCH->>GEMINI: Enrich qualifying job
            GEMINI-->>MATCH: AI enrichment
        end

        MATCH-->>PIPE: ResumeMatchResult

    end

    PIPE->>PIPE: Rank by overall_score

    PIPE->>SELECT: Final selection

    SELECT-->>PIPE: Selected / rejected jobs

    PIPE->>SHEETS: Export selected jobs

    SHEETS-->>PIPE: Export status

    PIPE-->>API: SearchResponse

    API-->>N8N: HTTP response
```

---

## 21. Responsibility Boundaries

### n8n

```text
Scheduling
Workflow triggering
HTTP invocation
Workflow orchestration
```

### FastAPI

```text
HTTP endpoint
Request handling
Pipeline invocation
Response handling
```

### SearchPipeline

```text
End-to-end orchestration
Stage ordering
Pipeline coordination
```

### SearchOrchestrator

```text
Provider execution
Provider result aggregation
Canonical job collection
```

### Providers

```text
External job acquisition
Provider-specific handling
Normalization
Canonical Job creation
```

### EnrichmentPipeline

```text
Skill extraction
Role classification
Deterministic enrichment
```

### ResumeMatcher

```text
Skill matching
Experience matching
Career progression
Location scoring
Company scoring
Freshness scoring
Final weighted score
Optional Gemini enrichment
```

### FinalSelectionEngine

```text
Eligibility
Final bucket
Final reason
Final priority
```

### GoogleSheetsService

```text
Selected-job export
Pipeline audit export
```

---

## 22. Local Runtime Boundary

The currently validated deployment runs locally:

```text
Windows Machine
      |
      +--> Python virtual environment
      |
      +--> FastAPI
      |
      +--> n8n
      |
      +--> External provider access
      |
      +--> Google Sheets credentials
      |
      +--> Gemini credentials
```

The local API boundary is:

```text
n8n
 |
 v
127.0.0.1:8000
 |
 v
FastAPI
```

This means the current deployment is a local production-style workflow and not yet an always-on public cloud deployment.

---

## 23. Core Architectural Sequence

The most important system boundary is:

```text
External Providers
        |
        v
Provider Layer
        |
        v
Canonical Job
        |
        v
Core Search Pipeline
        |
        +--> Deduplication
        +--> Freshness
        +--> Enrichment
        +--> Resume Matching
        +--> Weighted Scoring
        +--> Ranking
        +--> Final Selection
        |
        v
Application Queue
        |
        v
Google Sheets / Downstream Workflow
```

The architecture keeps the following concerns separate:

```text
Provider acquisition
        !=
Candidate scoring
        !=
Final selection
        !=
Application execution
        !=
Scheduling
```

This separation allows each layer to be tested and changed independently.

---

## 24. Final Sequence Summary

```text
n8n Schedule
      |
      v
FastAPI
      |
      v
SearchPipeline
      |
      v
SearchOrchestrator
      |
      v
Providers
      |
      v
Canonical Job
      |
      v
Deduplication
      |
      v
Freshness Filtering
      |
      v
Deterministic Enrichment
      |
      v
ResumeMatcher
      |
      +--> Skill Match
      +--> Experience Match
      +--> Career Progression
      +--> Location
      +--> Company
      +--> Freshness
      |
      v
FinalScoreCalculator
      |
      v
Optional Gemini Enrichment
      |
      v
Ranking
      |
      v
FinalSelectionEngine
      |
      v
Application Queue
      |
      v
Google Sheets
      |
      v
SearchResponse
      |
      v
FastAPI
      |
      v
n8n
```

The central principle is:

```text
External-source complexity
        |
        v
Provider Boundary
        |
        v
Canonical Job
        |
        v
Deterministic Business Logic
        |
        v
Final Selection
        |
        v
Downstream Application Workflow
```
