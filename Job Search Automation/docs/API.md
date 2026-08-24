# API

## Health

### `GET /health`

Checks whether the local FastAPI application is running.

Example:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

Expected:

```text
status
------
healthy
```

## Search

### `POST /jobs/search`

Executes the production search pipeline.

The endpoint intentionally delegates orchestration to `SearchPipeline`; it does not duplicate provider or scoring logic.

Example:

```powershell
Invoke-RestMethod `
    -Method POST `
    -Uri "http://127.0.0.1:8000/jobs/search"
```

Successful response contains:

```text
provider
jobs
total_found
total_returned
success
message
```

Each job uses the canonical internal job schema.

## OpenAPI

When FastAPI is running:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

These URLs are local-development endpoints and are not public production URLs.

## Error behavior

Pipeline exceptions are converted into an HTTP 500 response with a pipeline failure message.

External provider failures should be handled at the provider/orchestration layer rather than by duplicating fallback logic in the HTTP endpoint.
