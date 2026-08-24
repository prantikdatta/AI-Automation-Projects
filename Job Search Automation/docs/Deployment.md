# Deployment

## Current deployment model

The validated deployment is local:

```text
Windows machine
    |
    +-- Python virtual environment
    |
    +-- FastAPI application
    |
    +-- n8n
    |
    +-- local credentials
```

## Start the API

From:

```text
F:\CodeBasics\VS CODE\job-search-automation
```

activate the virtual environment and start the FastAPI application using the project's configured application server.

Then verify:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

## Manual production trigger

```powershell
Invoke-RestMethod `
    -Method POST `
    -Uri "http://127.0.0.1:8000/jobs/search"
```

A successful production run should end with a successful pipeline message and Google Sheets export.

## n8n scheduling

The n8n workflow should call:

```text
POST http://127.0.0.1:8000/jobs/search
```

For local scheduling to work:

- n8n must be running.
- FastAPI must be running.
- The computer must be powered on and available.
- Local credentials must be available.
- Network access to external providers must be available.

Closing VS Code does not inherently stop a separately running process, but closing the terminal that owns the process or stopping the Python process does.

## Important local limitation

A `127.0.0.1` endpoint exists only on the local machine.

Therefore this is **not yet an always-on hosted SaaS/product deployment**.

To make it unattended and continuously available, move the API and/or scheduler to an always-on server or cloud environment.

## Credentials

Keep these outside Git:

```text
.env
credentials/google-service-account.json
```

The public repository should contain only placeholders and setup instructions.

## Production hardening before public cloud deployment

Recommended future work:

- secret manager integration
- persistent database for application history
- retry and dead-letter handling
- structured observability
- provider quota monitoring
- health checks
- hosted n8n or equivalent scheduler
- authentication on public API endpoints
- rate limiting
