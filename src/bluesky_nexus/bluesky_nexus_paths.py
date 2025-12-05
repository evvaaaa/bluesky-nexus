"""bluesky_nexus_paths.py.

Utility functions for retrieving NeXus-related directory paths from
environment variables. These paths control where NeXus output files
and writer log files are stored—particularly important in containerized
deployments where configuration is passed exclusively via environment
variables.

Functions
---------
get_nx_file_dir_path()
    Return the directory where NeXus files should be written, taken from
    the `_NX_FILE_DIR_PATH` environment variable.

get_nx_log_file_dir_path()
    Return the directory where NeXus log files should be written, taken
    from the `_NX_LOG_FILE_DIR_PATH` environment variable.

Usage
-----
Configure the environment variables before using these functions. For example:

    from bluesky_nexus_paths import (
        get_nx_file_dir_path,
        get_nx_log_file_dir_path,
    )

    nexus_file_dir: Path = get_nx_file_dir_path()
    nexus_log_dir: Path = get_nx_log_file_dir_path()

Environment Variables
---------------------
_NX_FILE_DIR_PATH
    Directory where NeXus output files will be stored.

_NX_LOG_FILE_DIR_PATH
    Directory where the NeXus writer logs will be stored.

Notes
-----
If a required environment variable is not set, the function raises a
ValueError with a descriptive message.
"""

import os
from pathlib import Path

from bluesky_nexus.common.logging_utils import logger


def get_nx_file_dir_path() -> Path:
    """Return the NeXus file output directory as a Path.

    This function retrieves the value of the `_NX_FILE_DIR_PATH` environment
    variable. If it is not defined, a `ValueError` is raised.

    Returns
    -------
    Path
        The directory where NeXus files should be written.

    Raises
    ------
    ValueError
        If `_NX_FILE_DIR_PATH` is not defined.
    """
    # Extract from env variable nexus file dir path (in container)
    nx_file_dir_path = os.environ.get("_NX_FILE_DIR_PATH")
    if nx_file_dir_path is None:
        logger.error(
            "Environment variable '_NX_FILE_DIR_PATH' is not set. "
            "Unable to retrieve NeXus file directory path."
        )
        raise ValueError("Environment variable '_NX_FILE_DIR_PATH' is not set.")
    logger.debug("Retrieved NeXus file directory path: %s", nx_file_dir_path)
    return Path(nx_file_dir_path)


def get_nx_log_file_dir_path() -> Path:
    """Return the NeXus log file directory as a Path.

    This function retrieves the value of the `_NX_LOG_FILE_DIR_PATH`
    environment variable. If it is not defined, a `ValueError` is raised.

    Returns
    -------
    Path
        The directory where writer log files should be stored.

    Raises
    ------
    ValueError
        If `_NX_LOG_FILE_DIR_PATH` is not defined.
    """
    # Extract from env variable log file path (in container)
    nx_log_file_dir_path = os.environ.get("_NX_LOG_FILE_DIR_PATH")
    if nx_log_file_dir_path is None:
        logger.error(
            "Environment variable '_NX_LOG_FILE_DIR_PATH' is not set. "
            "Unable to retrieve NeXus log file directory path."
        )
        raise ValueError("Environment variable '_NX_LOG_FILE_DIR_PATH' is not set.")
    logger.debug("Retrieved NeXus log file directory path: %s", nx_log_file_dir_path)
    return Path(nx_log_file_dir_path)
