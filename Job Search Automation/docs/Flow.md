# Pipeline Flow

## End-to-end execution

```text
1. n8n Schedule Trigger
        |
2. POST /jobs/search
        |
3. SearchOrchestrator
        |
4. Provider / ATS collection
        |
5. Canonical Job objects
        |
6. Deduplication
        |
7. Freshness filtering
        |
8. Deterministic enrichment
        |
9. Resume matching
        |
10. Weighted scoring
        |
11. Ranking
        |
12. Final selection
        |
13. Google Sheets export
        |
14. SearchResponse
```

## Stage details

### Stage 1 — Collection

The search orchestrator gathers jobs from the configured API and ATS sources.

### Stage 2 — Deduplication

Duplicate opportunities are removed before downstream enrichment and scoring.

### Stage 3 — Freshness

Stale postings are filtered before expensive downstream processing.

### Stage 4 — Enrichment

Known skills are extracted and job roles are classified deterministically.

### Stage 5 — Resume matching

The candidate/job match is calculated from deterministic components.

### Stage 6 — Score

The final score is calculated from the configured weights.

### Stage 7 — Ranking

Evaluated jobs are ordered by the production score and posting priority.

### Stage 8 — Final selection

Only jobs satisfying the final role/location/score gates enter the final queue.

### Stage 9 — Export

Selected jobs are mapped to the Google Sheets schema and appended to the `Jobs` worksheet.

## Example production result

A successful run can look like:

```text
Evaluated jobs : 20
Selected jobs  : 6
Rejected jobs  : 14

Google Sheets:
6 jobs exported
```

The exact counts vary by provider availability and current job-market results.
