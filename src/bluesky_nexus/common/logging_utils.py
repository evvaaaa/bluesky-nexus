"""logging_utils.py.

This module provides utilities for setting up and managing logging for the
`bluesky_nexus` package. It supports both console-based logging and file-based
logging with automatic log rotation. The module is designed to simplify
logging configuration and ensure robust log management in both development and
production environments.

Features:
    - A pre-configured logger (`bluesky_nexus`) with a default `NullHandler`
      to prevent accidental log output.
    - The `setup_nx_logger` function to configure logging with:
        - Customizable logging levels for console and file outputs.
        - Console and file logging.
        - Automatic file naming and log rotation for file-based logging.

File-based Logging:
    - Log files are created in a specified directory.
    - A consistent filename is used (e.g., `nx_log.log`).
    - Log rotation is handled automatically when files exceed
      a specified size.
    - A fixed number of backup log files are retained to manage storage
      efficiently.

Usage:
    1. Import the logger and setup function in your application:
        >>> from logging_utils import setup_nx_logger, logger, LogLevel
    2. Configure the logger at the start of your application:
        >>> setup_nx_logger(
                console_level=LogLevel.DEBUG,
                file_level=LogLevel.INFO,
                log_file_dir_path="/path/to/logs", # Set to None to disable file logging
                log_file_name="myapp.log",         # Optional custom log filename
                max_file_size=5 * 1024 * 1024,     # 5 MB max per log file
                backup_count=3                     # Keep 3 rotated backups
            )
    3. Use `logger` anywhere in your code:
        >>> logger.debug("This is a debug message.")
        >>> logger.info("Starting application.")
        >>> logger.warning("This might be a problem.")
        >>> logger.error("An error occurred.")
        >>> logger.critical("Critical failure!")

Notes:
    - If `log_file_dir_path` is None or the directory cannot be created,
      file logging will be disabled automatically.
    - Log rotation helps prevent log files from growing too large.
    - Customize the log format via `log_format` parameter in `setup_nx_logger`.
    - By default, console logs show ERROR level and above, file logs DEBUG and above.
"""

import logging
import os
import traceback
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import Optional, Union

from bluesky_nexus.bluesky_nexus_const import DEFAULT_NX_LOG_FORMAT


class LogLevel(Enum):
    """Enum representing logging levels."""

    DEBUG = logging.DEBUG
    """Logging level for debug messages (numeric value 10)."""
    INFO = logging.INFO
    """Logging level for informational messages (numeric value 20)."""
    WARNING = logging.WARNING
    """Logging level for warnings (numeric value 30)."""
    ERROR = logging.ERROR
    """Logging level for errors (numeric value 40)."""
    CRITICAL = logging.CRITICAL
    """Logging level for critical errors (numeric value 50)."""


# Public API of this module: logging setup function, logger instance, and LogLevel
# constants
__all__ = [
    "setup_nx_logger",
    "logger",
    "LogLevel",
]

# Create a custom logger for the package
logger: logging.Logger = logging.getLogger(name="bluesky_nexus")

# Add a NullHandler by default to prevent unwanted logging
# if user doesn't call setup_nx_logger.
logger.addHandler(logging.NullHandler())


# pylint: disable=too-many-arguments,too-many-positional-arguments
def setup_nx_logger(
    console_level: Union[int, LogLevel] = LogLevel.ERROR,
    file_level: Union[int, LogLevel] = LogLevel.DEBUG,
    log_file_dir_path: Optional[str] = None,
    log_file_name: str = "nx_log.log",
    log_format: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """Configure the logger with console and file handlers.

    This function sets up the `bluesky_nexus` logger with customizable
    logging levels for console and file output. File logging includes
    automatic log rotation and retention of backup log files.

    Parameters:
        console_level (int or LogLevel, optional): Logging level for console output.
        file_level (int or LogLevel, optional): Logging level for file output.
        log_file_dir_path (str, optional): Directory where log files will
            be stored. If None, file logging is disabled.
        log_file_name (str, optional): Name of the log file.
            Defaults to "nx_log.log".
        log_format (str, optional): Log message format. If not provided,
            uses DEFAULT_NX_LOG_FORMAT.
        max_file_size (int, optional): Maximum size (in bytes) of a log file
            before it is rotated. Defaults to 10 MB.
        backup_count (int, optional): Number of backup log files to keep
            after rotation. Defaults to 5.
        enable_console (bool, optional): Enable console logging. Defaults to True.
        enable_file (bool, optional): Enable file logging. Defaults to True.
    """
    # Convert LogLevel enums to their int values since setLevel()
    # expects an int, not an enum.
    console_level = _get_level_value(console_level)
    file_level = _get_level_value(file_level)

    if log_format is None:

        log_format = DEFAULT_NX_LOG_FORMAT or (
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s - "
            "%(funcName)s  %(message)s"
        )

    formatter = logging.Formatter(log_format)

    # Set logger's level to fixed value to let all log levels pass through
    logger.setLevel(logging.DEBUG)

    # Remove all existing handlers before configuring new handlers
    _remove_all_handlers(logger)

    # Prevent messages from propagating to the root logger
    logger.propagate = False

    # Add NullHandler if no output is desired
    if not enable_console and not enable_file:
        logger.addHandler(logging.NullHandler())
        return

    # Configure file logging if log_file_dir_path is provided
    if enable_file and log_file_dir_path:

        try:
            # Ensure the directory exists
            os.makedirs(log_file_dir_path, exist_ok=True)
        except OSError as e:
            logger.error(
                "Failed to create log directory '%s': %s. File logging disabled.",
                log_file_dir_path,
                e,
            )
            # Optional: Log the full traceback for deeper debugging
            logger.debug(
                "Traceback for directory creation failure:\n%s", traceback.format_exc()
            )
            enable_file = False  # disable file logging

        if enable_file:
            log_file_path = os.path.join(log_file_dir_path, log_file_name)
            # Create a RotatingFileHandler for log rotation
            file_handler = RotatingFileHandler(
                log_file_path,
                mode="a",
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    if enable_console:
        # Configure console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info(
        "Logging setup complete. Console logging: %s (level: %s), "
        "File logging: %s (level: %s)",
        "enabled" if enable_console else "disabled",
        logging.getLevelName(console_level),
        "enabled" if enable_file else "disabled",
        logging.getLevelName(file_level),
    )


def _remove_all_handlers(log: logging.Logger) -> None:
    """Remove all handlers from the given logger.

    This function is used internally by `setup_nx_logger` and is not part of
    the public API.

    This function iterates over all handlers currently attached to the
    specified logger, removes and closes them. It is particularly useful when
    reconfiguring a logger to avoid duplicate logging outputs.

    Parameters:
        log (logging.Logger): The logger instance whose handlers will be removed.
    """
    for handler in log.handlers[:]:
        # Use a copy of the handlers list to avoid modification during iteration
        log.removeHandler(handler)
        # Close the handler to release any associated resources
        handler.close()


def _get_level_value(level: Union[int, Enum]) -> int:
    """Get level value as integer.

    This helper function ensures compatibility with the logging
    module's `setLevel()` method, which expects an integer level.
    Convert a LogLevel enum member to its integer value or return the
    integer level as-is.

    Parameters:
        level (int or LogLevel): The logging level, either as an int or LogLevel enum.

    Returns:
        int: The integer logging level suitable for logger configuration.
    """
    if isinstance(level, Enum) and level.__class__.__name__ == "LogLevel":
        return level.value

    assert not isinstance(level, Enum), "level should not be Enum here"
    return level
