import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """
    Central application logger.

    Features
    --------
    - Console logging
    - Rotating log files
    - Shared singleton logger
    - Standard formatting
    """

    _logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:

        if cls._logger is not None:
            return cls._logger

        log_directory = Path("logs")
        log_directory.mkdir(exist_ok=True)

        logger = logging.getLogger("job_search_automation")

        logger.setLevel(logging.INFO)

        logger.propagate = False

        if logger.handlers:
            cls._logger = logger
            return logger

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            filename=log_directory / "application.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        logger.addHandler(file_handler)

        cls._logger = logger

        return logger


logger = Logger.get_logger()