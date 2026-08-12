"""Logger module for bluesky-nexus."""

import logging
import sys
import time
from typing import Any, Callable

LOGGER = logging.getLogger("bluesky_nexus")

# This makes the logger silent unless the user adds a handler.
LOGGER.addHandler(logging.NullHandler())


def setup_logging(level: str = "INFO") -> None:
    """Configure the project's logging.
    This function should be called once at the application entry point.

    Args:
        level: Logging level as a string (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure the ROOT logger so that dependencies
    # also follow this configuration if needed, or use LOGGER.propagate.
    # We use force=True to ensure our config overrides any default handlers.
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Ensures this config takes precedence
    )
