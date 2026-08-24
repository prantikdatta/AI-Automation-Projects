# Data Model

## Purpose

The system uses a canonical internal job model so that provider-specific payloads do not leak into downstream pipeline stages.

Every provider converts its external response into the canonical `Job` model.

```text
External Provider
       |
       v
Provider Normalizer
       |
       v
CanonicalMapper
       |
       v
Job
       |
       +--> Deduplication
       +--> Freshness
       +--> Enrichment
       +--> Resume Matching
       +--> Ranking
       +--> Final Selection
       +--> Application Queue
       +--> Google Sheets
```

---

## 1. Job

Primary model:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\models\job.py
```

The `Job` model represents one canonical job opportunity.

### Identity and search context

| Field           | Purpose                          |
| --------------- | -------------------------------- |
| `searched_role` | Role/query that produced the job |
| `run_date`      | Pipeline execution timestamp     |
| `title`         | Job title                        |
| `company`       | Employer                         |
| `location`      | Job location                     |
| `source`        | External job source              |
| `provider`      | Provider that supplied the job   |

### Job content

| Field             | Purpose                          |
| ----------------- | -------------------------------- |
| `description`     | Job description                  |
| `job_url`         | Canonical job/application URL    |
| `posted_at`       | Original posting timestamp       |
| `employment_type` | Full-time, contract, etc.        |
| `seniority`       | Job seniority                    |
| `remote`          | Whether remote work is supported |
| `work_mode`       | Remote, hybrid, on-site          |
| `skills`          | Extracted skills                 |

### Compensation

| Field               | Purpose                         |
| ------------------- | ------------------------------- |
| `salary_min`        | Minimum salary                  |
| `salary_max`        | Maximum salary                  |
| `currency`          | Salary currency                 |
| `salary_confidence` | Confidence in salary extraction |

---

## 2. Enrichment Fields

Deterministic enrichment adds structured information to the canonical job.

```text
Job
 |
 +--> skills
 +--> matched_skills
 +--> missing_skills
 +--> company_tier
 +--> job_bucket
```

Important fields:

| Field            | Purpose                                   |
| ---------------- | ----------------------------------------- |
| `skills`         | Skills extracted from description         |
| `matched_skills` | Candidate skills found in job             |
| `missing_skills` | Relevant candidate skills absent from job |
| `company_tier`   | Employer classification                   |
| `job_bucket`     | Job-family classification                 |

---

## 3. Matching and Scoring

The intelligence layer calculates multiple deterministic components.

```text
Job
 |
 +--> Skill Match
 +--> Experience Match
 +--> Career Progression
 +--> Location Match
 +--> Company Score
 +--> Freshness Score
          |
          v
   FinalScoreCalculator
          |
          v
     overall_score
```

Current weights:

| Component          |   Weight |
| ------------------ | -------: |
| Skills             |      30% |
| Experience         |      20% |
| Career progression |      15% |
| Location           |      10% |
| Company            |      10% |
| Freshness          |      15% |
| **Total**          | **100%** |

The weights are defined in:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\config\final_score_weights.py
```

---

## 4. Recommendation Fields

The scoring layer may populate:

```text
overall_score
recommendation
overall_explanation
apply_priority
shortlist_likelihood_score
shortlist_bucket
blunt_reason
resume_match_result
```

The deterministic overall score remains the authoritative score.

Gemini enrichment is supplementary and must not replace the deterministic scoring path.

---

## 5. Final Selection

Final selection fields:

```text
final_selection_eligible
final_selection_bucket
final_selection_reason
final_selection_priority
```

The selection layer determines whether a scored job is eligible for the final application queue.

```text
Scored Job
    |
    v
FinalSelectionEngine
    |
    +--> Eligible
    |      |
    |      v
    |   Application Queue
    |
    +--> Rejected
```

---

## 6. Application Tracking

Application lifecycle fields include:

```text
application_status
```

Default:

```text
Not Applied
```

The application layer can subsequently maintain queue and execution state without changing the canonical provider contract.

---

## 7. Resume Tailoring

The model also supports:

```text
tailored_resume_reason
tailored_resume_text
```

These fields are downstream application-preparation outputs.

They are not required for job discovery.

---

## 8. Raw Provider Payload

The `raw` field retains the original provider payload when available.

```text
raw: Dict[str, Any]
```

Purpose:

* debugging
* provider normalization investigation
* auditability
* future provider improvements

Raw payloads must not contain credentials.

---

## 9. SearchRequest

Primary model:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\models\request.py
```

A `SearchRequest` provides the canonical input to providers.

Important fields:

```text
searched_role
keywords
locations
bucket
roles
priority
limit
remote_only
posted_within_days
providers
```

The model supports both legacy single-role providers and the newer bucket-based search strategy.

---

## 10. SearchResponse

Primary model:

```text
F:\CodeBasics\VS CODE\job-search-automation\src\job_search_automation\models\response.py
```

Every provider returns:

```text
SearchResponse
 |
 +--> provider
 +--> jobs
 +--> total_found
 +--> total_returned
 +--> success
 +--> message
```

This creates a stable contract between providers and the pipeline.

---

## 11. Data Ownership

| Data               | Owner                 |
| ------------------ | --------------------- |
| External payload   | Provider              |
| Canonical `Job`    | Normalizer / mapper   |
| Deduplication      | Pipeline              |
| Freshness          | Pipeline              |
| Enrichment         | Enrichment layer      |
| Candidate matching | Intelligence layer    |
| Final selection    | Selection layer       |
| Application queue  | Application layer     |
| Reporting/export   | Google Sheets service |
| Scheduling         | n8n                   |

---

## 12. Core Design Principle

The most important data-model rule is:

```text
Provider-specific data
        |
        v
Canonical Job
        |
        v
All downstream processing
```

Downstream components should consume `Job`, not RapidAPI, Apify, Greenhouse, Ashby, or other provider-specific response structures.
