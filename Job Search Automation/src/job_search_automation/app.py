from __future__ import annotations

from fastapi import FastAPI

from job_search_automation.api.health import router as health_router
from job_search_automation.api.jobs import router as jobs_router
from job_search_automation.core.logger import logger
from job_search_automation.core.settings import settings


app = FastAPI(
    title=settings.API_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

app.include_router(health_router)
app.include_router(jobs_router)


@app.on_event("startup")
async def startup() -> None:
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Application stopped")