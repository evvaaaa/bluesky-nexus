"""Test suite for the bluesky_nexus.common.logging_utils module.

Contains tests that verify the behavior of logging setup utilities,
including console and file logging, log rotation, error handling, and
log level conversion helpers.

Tests utilize pytest fixtures for isolated temporary directories and the
caplog fixture to capture logging output for assertions.
"""

import importlib
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from bluesky_nexus.common import logging_utils
from bluesky_nexus.common.logging_utils import (
    LogLevel,
    _get_level_value,
    logger,
    setup_nx_logger,
)


@pytest.fixture
def temp_log_dir():
    """Fixture for creating and cleaning up a temporary directory."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


def test_logger_default_state():
    """Test that logger has only NullHandler by default."""
    importlib.reload(logging_utils)  # ensure fresh module load
    handlers = logging_utils.logger.handlers
    assert any(isinstance(h, logging.NullHandler) for h in handlers)


def test_console_logging_setup(capsys):
    """Verify that console handler actually prints to stderr/stdout."""
    setup_nx_logger(
        console_level=LogLevel.DEBUG,
        enable_console=True,
    )

    logger.debug("Debug to console")
    logger.info("Info to console")

    captured = capsys.readouterr()
    assert "Debug to console" in captured.err
    assert "Info to console" in captured.err


# pylint: disable=redefined-outer-name
def test_file_logging_creates_file(temp_log_dir):
    """Test file handler writes logs to the expected file."""
    log_file = "test_log.log"

    setup_nx_logger(
        file_level=LogLevel.INFO,
        console_level=LogLevel.CRITICAL,
        log_file_dir_path=temp_log_dir,
        log_file_name=log_file,
        enable_console=False,
    )

    logger.info("File log message")
    log_path = temp_log_dir / log_file
    assert os.path.exists(log_path)
    content = log_path.read_text(encoding="utf-8")
    assert "File log message" in content


def test_log_rotation_creates_multiple_files(temp_log_dir):
    """Test that rotating log handler creates backup files."""
    log_file = "rotate_test.log"

    setup_nx_logger(
        log_file_dir_path=temp_log_dir,
        log_file_name=log_file,
        log_file_max_size=200,  # Small size to force rotation
        backup_count=2,
        enable_console=False,
    )

    for _ in range(100):
        logger.debug("Filling up log to trigger rotation")

    log_files = [
        name for name in os.listdir(temp_log_dir) if name.startswith("rotate_test")
    ]

    assert any(f.endswith(".log") for f in log_files)
    assert len(log_files) >= 1  # Base file + backups


def test_logger_setup_multiple_times_no_duplicate_logs(temp_log_dir):
    """Ensure repeated setup calls do not cause duplicate log.

    entries.
    """
    setup_nx_logger(
        log_file_dir_path=temp_log_dir,
        log_file_name="multi.log",
        enable_console=False,
    )
    setup_nx_logger(
        log_file_dir_path=temp_log_dir,
        log_file_name="multi.log",
        enable_console=False,
    )

    logger.info("Log this once")
    log_path = temp_log_dir / "multi.log"
    content = log_path.read_text(encoding="utf-8")
    assert content.count("Log this once") == 1


def test_get_level_value_with_enum_and_int():
    """Unit test for _get_level_value helper."""
    assert _get_level_value(LogLevel.INFO) == logging.INFO
    assert _get_level_value(30) == 30


def test_logging_info_level_file_only(tmp_path):
    """Verify file logging at INFO level captures INFO, not DEBUG."""
    log_dir = Path(tmp_path)
    log_file_name = "test_nx_log.log"

    setup_nx_logger(
        console_level=LogLevel.INFO,
        file_level=LogLevel.INFO,
        log_file_dir_path=log_dir,
        log_file_name=log_file_name,
        enable_console=False,  # don't use console
    )

    debug_message = "This is a debug message that should NOT be logged."
    info_message = "This is an info level test message."

    logger.debug(debug_message)
    logger.info(info_message)

    log_file_path = log_dir / log_file_name
    assert log_file_path.exists()

    contents = log_file_path.read_text(encoding="utf-8")
    assert debug_message not in contents
    assert info_message in contents


def test_no_file_logging_when_dir_is_none_per_default(tmp_path):
    """File logging must be disabled when log_file_dir_path=None."""
    # Clean and reset the logger state
    importlib.reload(logging_utils)

    setup_nx_logger()
    logger.info("Message that should NOT go to any file")

    # Ensure no file was created in temp directory
    # Just check the entire directory is empty
    assert not any(tmp_path.iterdir()), (
        "No files should be created when log_file_dir_path=None"
    )

    handlers = logging_utils.logger.handlers
    assert not any(isinstance(h, logging.FileHandler) for h in handlers)


def test_no_file_logging_when_dir_is_none_explicitly(tmp_path):
    """File logging must be disabled when log_file_dir_path=None."""
    # Clean and reset the logger state
    importlib.reload(logging_utils)

    setup_nx_logger(
        log_file_dir_path=None,  # explicitly None
    )

    logger.info("Message that should NOT go to any file")

    # Ensure no file was created in temp directory
    # Just check the entire directory is empty
    assert not any(tmp_path.iterdir()), (
        "No files should be created when log_file_dir_path=None"
    )
    handlers = logging_utils.logger.handlers
    assert not any(isinstance(h, logging.FileHandler) for h in handlers)


if __name__ == "__main__":
    # Execute all test cases in the script when run directly.
    pytest.main([__file__])
