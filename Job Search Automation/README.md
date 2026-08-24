# Job Search Automation

An end-to-end job discovery and ranking pipeline that collects jobs from multiple providers, normalizes and deduplicates them, applies freshness and relevance filters, scores them against a candidate profile, performs optional Gemini enrichment, selects the strongest opportunities, and exports the final queue to Google Sheets.

## What the system does

```text
Scheduled n8n workflow
        |
        v
FastAPI /jobs/search
        |
        v
Search Orchestrator
        |
        +--------------------+
        |                    |
        v                    v
API Providers           ATS Providers
RapidAPI / Apify        Greenhouse / Ashby / ...
        |                    |
        +---------+----------+
                  |
                  v
          Canonical Job Model
                  |
                  v
            Deduplication
                  |
                  v
          Freshness Filtering
                  |
                  v
       Deterministic Enrichment
       - skill extraction
       - role classification
                  |
                  v
          Resume Matching
       - skills
       - experience
       - career progression
       - location
       - company
       - freshness
                  |
                  v
          Weighted Final Score
                  |
                  v
          Final Selection
                  |
                  v
          Google Sheets / Jobs
                  |
                  v
          SearchResponse
```

## Current production boundary

The authoritative production entrypoint is:

```text
POST /jobs/search
```

The pipeline itself remains responsible for orchestration. Providers translate external job sources into the canonical internal `Job` model; downstream stages consume that model rather than provider-specific payloads.

## Main components

| Layer | Responsibility |
|---|---|
| `api/` | FastAPI HTTP boundary |
| `orchestrators/` | End-to-end pipeline coordination |
| `providers/` | External job-source integrations |
| `ats/` | ATS-specific ingestion and filtering |
| `normalizers/` | Provider payload normalization |
| `enrichment/` | Deterministic job enrichment |
| `intelligence/` | Resume matching, scoring and final selection |
| `filtering/` | Early deterministic rejection |
| `matching/` | Matching utilities and compatibility logic |
| `ranking/` | Ranking utilities |
| `services/google_sheets/` | Google Sheets persistence |
| `n8n/` | Automation integration boundary |
| `application/` | Application readiness, queue and execution workflow |
| `tests/` / `src/tests/` | Regression and production validation |

## Scoring model

The final deterministic score is weighted across:

- Skills — 30%
- Experience — 20%
- Career progression — 15%
- Location — 10%
- Company — 10%
- Freshness — 15%

The weighted components sum to 100%.

Gemini is an enrichment layer; deterministic scoring remains the source of truth.

## Final selection

The final selection layer checks target role families, target locations/remote eligibility and score thresholds before placing jobs into the final application queue.

The final output can contain buckets such as:

```text
A - Apply
B - Strong Match
C - Review
Reject
```

The exact bucket assignment is controlled by the current selection implementation.

## Output

Selected jobs are mapped into the Google Sheets `Jobs` worksheet. The pipeline also returns a canonical `SearchResponse` through the API.

## Local setup

1. Create a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create a local `.env` from `.env.example`.
4. Add your own API credentials locally.
5. Configure Google service-account credentials locally.
6. Start the FastAPI application.
7. Trigger `/jobs/search` manually before enabling automation.

Example health check:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

Example pipeline trigger:

```powershell
Invoke-RestMethod `
    -Method POST `
    -Uri "http://127.0.0.1:8000/jobs/search"
```

## n8n

n8n is the scheduler/orchestration boundary for the local deployment:

```text
n8n Schedule Trigger
        |
        v
POST /jobs/search
        |
        v
Pipeline
        |
        v
Google Sheets
```

For the local setup, the FastAPI process and n8n process must both be running when the scheduled workflow is expected to execute.

A local `127.0.0.1` endpoint is not a public production endpoint. For unattended execution, the machine must remain available or the API/n8n components must later be moved to an always-on hosted environment.

## Security

Never commit:

- `.env`
- API keys
- Google service-account JSON
- private resume files
- private Google Sheet identifiers if treated as sensitive
- logs containing personal or credential information
- generated debugging payloads

Use `.env.example` only for variable names and placeholders.

## Project status

The production pipeline has been manually executed successfully through the API and scheduled n8n workflow, including final Google Sheets export.

The repository is being prepared as a public engineering portfolio project. Public documentation describes the architecture without exposing personal credentials or private candidate data.
