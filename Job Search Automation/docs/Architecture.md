# Architecture

## System boundary

The system has four major boundaries:

1. **Automation boundary** — n8n schedules execution.
2. **API boundary** — FastAPI exposes `/jobs/search`.
3. **Pipeline boundary** — `SearchPipeline` orchestrates the production flow.
4. **Persistence boundary** — Google Sheets receives the selected job queue.

## Production flow

```text
                    +----------------------+
                    |       n8n            |
                    | Schedule Trigger     |
                    +----------+-----------+
                               |
                               | POST /jobs/search
                               v
                    +----------------------+
                    |       FastAPI        |
                    |    API boundary      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  SearchPipeline      |
                    |  orchestration       |
                    +----------+-----------+
                               |
               +---------------+----------------+
               |                                |
               v                                v
      +------------------+             +------------------+
      | API Providers    |             | ATS Providers   |
      | RapidAPI         |             | Greenhouse      |
      | Apify             |             | Ashby           |
      | JobSpy            |             | other ATS       |
      +--------+---------+             +---------+--------+
               |                                 |
               +---------------+-----------------+
                               |
                               v
                    +----------------------+
                    | Canonical Job model  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Deduplication        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Freshness filtering  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Enrichment           |
                    | Skills / Role        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | ResumeMatcher        |
                    | deterministic score  |
                    | + Gemini enrichment  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | FinalSelectionEngine |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Google Sheets        |
                    | Jobs worksheet       |
                    +----------------------+
```

## Provider abstraction

Providers implement a common contract:

```text
SearchRequest
     |
     v
Provider
     |
     v
SearchResponse
     |
     v
list[Job]
```

Provider-specific response structures do not propagate through the pipeline.

## Intelligence architecture

The authoritative scoring path is:

```text
Job
 |
 +-- SkillMatcher
 +-- ExperienceMatcher
 +-- CareerProgressionMatcher
 +-- LocationMatcher
 +-- CompanyScorer
 +-- FreshnessScorer
 |
 v
FinalScoreCalculator
 |
 v
ResumeMatchResult
 |
 +-- deterministic metadata
 +-- optional Gemini enrichment
 |
 v
FinalSelectionEngine
```

The final score weights are:

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

## Responsibilities

### Providers

Providers retrieve and translate external job data.

They do not own:

- ranking
- final selection
- Google Sheets export
- Gemini scoring
- application execution

### SearchPipeline

The pipeline coordinates the stages. It should not duplicate provider-specific logic.

### ResumeMatcher

The matcher performs deterministic candidate/job scoring and may use Gemini for enrichment. Deterministic scoring remains the source of truth.

### FinalSelectionEngine

The selection engine decides whether an evaluated job belongs in the final queue based on role, location/remote eligibility and score thresholds.

### Google Sheets

Sheets is the current persistence/reporting destination for selected jobs.

### n8n

n8n is the scheduling boundary, not the business-logic layer. The Python application remains the owner of the job-search logic.

## Application workflow

The broader application layer follows:

```text
Final Jobs
    |
    v
Application Readiness
    |
    v
Application Queue
    |
    v
Application Workflow
    |
    +--> Application Execution
    |
    +--> Execution Audit
    |
    v
Tracking / Sheets
```

The current production run validates the queue and execution boundary without silently submitting applications.

## Local versus hosted architecture

Current:

```text
Local machine
├── FastAPI
├── n8n
├── Python environment
└── credentials
```

Future hosted architecture can separate these into:

```text
Cloud scheduler / n8n
        |
        v
Hosted API
        |
        v
Pipeline workers
        |
        +--> external providers
        +--> Gemini
        +--> Google Sheets
```

That migration does not require changing the canonical pipeline contract.
