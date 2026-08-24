from pathlib import Path

from loguru import logger

from job_search_automation.core.settings import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sink=lambda message: print(message, end=""),
    level=settings.LOG_LEVEL,
    colorize=True,
)

logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level=settings.LOG_LEVEL,
    enqueue=True,
)

__all__ = ["logger"]