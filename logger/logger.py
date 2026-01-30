import logging
import sys

loggerInitialized = False


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    date_format: str | None = None,
) -> None:
    """
    Setup the root logger with console handler.

    Args:
        level: Logging level (default: logging.INFO)
        format_string: Custom format string for log messages
        date_format: Custom date format string
    """
    global loggerInitialized
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter
    formatter = logging.Formatter(fmt=format_string, datefmt=date_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our console handler
    root_logger.addHandler(console_handler)
    loggerInitialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured logger instance
    """
    global loggerInitialized
    if loggerInitialized:
        return logging.getLogger(name)
    else:
        raise SystemError("Initialize logger before use!")
