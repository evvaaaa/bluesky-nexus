"""Common utils used across submodules."""

from .logging_utils import LogLevel, setup_nx_logger

# Set up a default console logger.
setup_nx_logger(console_level=LogLevel.INFO)
