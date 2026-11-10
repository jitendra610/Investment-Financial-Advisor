import logging

from app.core.logging_config import setup_logging


def test_logging():

    # Initialize logging and create log file.
    log_file = setup_logging()

    # Create logger for this test.
    logger = logging.getLogger("test_logging")

    # Write messages.
    logger.info("TEST: Logging started")
    logger.warning("TEST: Warning message")
    logger.error("TEST: Error message")

    # Flush handlers to ensure messages are written.
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify log file exists.
    assert log_file.exists(), "Log file was not created"

    # Verify content.
    content = log_file.read_text(encoding="utf-8")

    assert "TEST: Logging started" in content
    assert "TEST: Warning message" in content
    assert "TEST: Error message" in content

    print(f"\nPASS: Log file created at {log_file}")


if __name__ == "__main__":
    test_logging()