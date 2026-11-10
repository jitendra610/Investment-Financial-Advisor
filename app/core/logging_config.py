import logging
from datetime import datetime
from pathlib import Path

# Project root directory.
BASE_DIR = Path(__file__).resolve().parents[2]

# Create logs directory.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging():

    # Generate today's log filename.
    today = datetime.now().strftime("%Y-%m-%d")

    log_file = LOG_DIR / f"investment_advisor_{today}.log"

    # Configure root logger.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Avoid duplicate file handlers.
    if not any(
        isinstance(handler, logging.FileHandler)
        and handler.baseFilename == str(log_file)
        for handler in logger.handlers
    ):
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Verify logging configuration.
    logger.info("Logging initialized: %s", log_file)

    return log_file