"""Utilities for configuring and managing logging in `bluesky_nexus`.

This module centralizes all logging configuration used across the
`bluesky_nexus` package. It provides a consistent, flexible logging setup
that supports both console logging and file logging with automatic
rotation, making it suitable for development, service deployments, and
production environments.

Main Features
-------------
- Provides a package-level logger (`bluesky_nexus`) with a default
  `NullHandler` to avoid emitting logs until explicitly configured.
- Offers `setup_nx_logger()`, a high-level function that configures:
    * Console logging with a selectable log level.
    * File logging with automatic directory creation.
    * Rotating log files to prevent unbounded log growth.
    * Customizable log formats and file names.

File Logging & Rotation
-----------------------
When file logging is enabled:
- Log files are written to the directory specified via `log_file_dir_path`.
- A single main log file is maintained (default: ``nx_log.log``).
- Rotation occurs automatically when the file exceeds the configured
  ``max_file_size``.
- A fixed number of rotated backups (``backup_count``) are retained.

Usage Example
-------------
Typical application setup:

    >>> from bluesky_nexus.common.logging_utils import (
    ...     setup_nx_logger, logger, LogLevel
    ... )
    >>> setup_nx_logger(
    ...     console_level=LogLevel.INFO,
    ...     file_level=LogLevel.DEBUG,
    ...     log_file_dir_path=Path("/path/to/logs"),
    ...     log_file_name="service.log",
    ...     max_file_size=5 * 1024 * 1024,
    ...     backup_count=3,
    ... )
    >>> logger.info("Application started.")
    >>> logger.debug("Detailed diagnostics message.")

Notes
-----
- If ``log_file_dir_path`` is ``None``, file logging is disabled.
- If ``log_file_dir_path`` is provided but the directory cannot be created or
  the log file cannot be opened, a ``RuntimeError`` is raised to avoid silent
  loss of file logging.
- Console and file logging can be independently enabled or disabled.
- If both output channels are disabled (no console, no file), a `NullHandler`
  is installed.
- The module uses `DEFAULT_NX_LOG_FORMAT` unless a custom format is provided.

Public API
----------
- setup_nx_logger
- logger
- LogLevel
"""

import logging
import time
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable


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
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG,
    log_file_dir_path: Path | None = None,
    log_file_name: str = "nx_log.log",
    log_format: str | None = None,
    log_file_max_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    enable_console: bool = True,
) -> None:
    """Configure the logger with console and file handlers.

    This function sets up the `bluesky_nexus` logger with customizable
    logging levels for console and file output. File logging includes
    automatic log rotation and retention of backup log files.

    File logging is enabled *only if* ``log_file_dir_path`` is not None.
    If ``log_file_dir_path`` is None, file logging is disabled.

    Parameters:
        console_level (int or LogLevel, optional): Logging level for console output.
        file_level (int or LogLevel, optional): Logging level for file output.
        log_file_dir_path (Path | None, optional): Directory where log files will
            be stored. If None, file logging is disabled.
        log_file_name (str, optional): Name of the log file.
            Defaults to "nx_log.log".
        log_format (str, optional): Log message format. If not provided,
            uses DEFAULT_NX_LOG_FORMAT.
        log_file_max_size (int, optional): Maximum size (in bytes) of a log file
            before it is rotated. Defaults to 10 MB.
        backup_count (int, optional): Number of backup log files to keep
            after rotation. Defaults to 5.
        enable_console (bool, optional): Enable console logging. Defaults to True.
    """
    if log_format is None:
        function_name_included = (
            " %(funcName)s - %(module)s -"
            if console_level.value <= LogLevel.DEBUG.value
            else ""
        )

        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s -"
            f"{function_name_included} %(message)s"
        )

    formatter = logging.Formatter(log_format)

    # Set logger's level to fixed value to let all log levels pass through
    logger.setLevel(logging.DEBUG)

    # Remove all existing handlers before configuring new handlers
    _remove_all_handlers(logger)

    # Prevent messages from propagating to the root logger
    logger.propagate = False

    # Add NullHandler if no output is desired
    if not enable_console and log_file_dir_path is None:
        logger.addHandler(logging.NullHandler())
        return

    # -------------------------
    # File logging (only when log_file_dir_path is defined)
    # -------------------------
    if log_file_dir_path is not None:
        try:
            # Ensure the directory exists
            log_file_dir_path.mkdir(parents=True, exist_ok=True)

        # Hard fail if mkdir fails
        except OSError as e:
            raise RuntimeError(
                f"Failed to create log directory '{log_file_dir_path}': {e}"
            ) from e

        log_file_path: Path = log_file_dir_path / log_file_name

        try:
            file_handler = RotatingFileHandler(
                log_file_path,
                mode="a",
                maxBytes=log_file_max_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
        # Hard fail if opening the log file fails
        except OSError as e:
            raise RuntimeError(
                f"Failed to create/open log file '{log_file_path}': {e}"
            ) from e

        file_handler.setLevel(file_level.value)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if enable_console:
        # Configure console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level.value)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info(
        "Logging setup complete. Console logging: %s (level: %s), "
        "File logging: %s (level: %s)",
        "enabled" if enable_console else "disabled",
        logging.getLevelName(console_level.value),
        "enabled" if log_file_dir_path is not None else "disabled",
        logging.getLevelName(file_level.value),
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


def log_time_taken(function: Callable):
    """Measure time.

    A decorator that measures the execution time of the decorated
    function.

    This decorator uses time.perf_counter() to calculate the time elapsed
    during the execution of the function and logs the result in seconds.
    """
    function_name = function.__name__

    def measure_time_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = function(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.info("%s executed in %.6f seconds", function_name, elapsed_time)
        return result

    return measure_time_wrapper
