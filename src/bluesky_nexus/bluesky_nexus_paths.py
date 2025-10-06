"""bluesky_nexus_paths.py.

This module provides utility functions for retrieving NeXus-related directory
paths and other configuration paths (e.g., log file path) from environment
variables. These paths are essential for configuring the locations of NeXus
files and logs in a containerized or environment-variable-driven setup.

Functions:
    get_nx_file_dir_path():
        Retrieves the directory path for storing NeXus files from the
        `_NX_FILE_DIR_PATH` environment variable. Raises an error if the
        variable is not set.

    get_nx_log_file_dir_path():
        Retrieves the NeXus log file dir path from the
        `_NX_LOG_FILE_DIR_PATH` environment variable. Raises an error if the
        variable is not set.

Usage:
    This module is designed to be imported into other scripts or modules
    where NeXus file paths, schema paths, or log file paths need to be
    dynamically resolved from environment variables. Ensure that the relevant
    environment variables are set in the system configuration
    (e.g., `~/etc/environment`) before using these functions.

Example:
    from bluesky_nexus_paths import get_nx_file_dir_path, get_log_file_path

    nexus_file_dir_path: str = get_nx_file_dir_path()
    nexus_log_file_dir_path: str = get_nx_log_file_dir_path()

Environment Variables:
    - `_NX_FILE_DIR_PATH`: The path to the directory where NeXus files will
      be stored.
    - `_NX_LOG_FILE_DIR_PATH`: The path to the NeXus log file dir used by
      the application.

Notes:
    - If the required environment variables are not set, the functions will
      raise a `ValueError` with a descriptive message.
    - This module is particularly suited for containerized environments where
      configuration is managed via environment variables.
"""

import os

from bluesky_nexus.common.logging_utils import logger


def get_nx_file_dir_path():
    """get_nx_file_dir_path.

    Retrieve the NeXus file directory path from the environment
    variable.

    This function checks the environment variable `_NX_FILE_DIR_PATH` to
    determine the directory path where NeXus files are to be stored. If the
    variable is not set, a `ValueError` is raised.

    Returns:
        str: The NeXus file directory path.

    Raises:
        ValueError: If the `_NX_FILE_DIR_PATH` environment variable is not
        defined.

    Notes:
        - The `_NX_FILE_DIR_PATH` variable must be set in the environment
          configuration file (e.g., `~/etc/environment`) for this function to
          work correctly.
        - This function is designed to be used in containerized environments
          where paths are configured via environment variables.
    """
    # Extract from env variable nexus file dir path (in container)
    nx_file_dir_path = os.environ.get("_NX_FILE_DIR_PATH")
    if nx_file_dir_path is None:
        logger.error(
            "Environment variable '_NX_FILE_DIR_PATH' is not set. "
            "Unable to retrieve NeXus file directory path."
        )
        raise ValueError(
            "_NX_FILE_DIR_PATH is None. Check content of ~/etc/environment."
        )
    logger.debug("Retrieved NeXus file directory path: %s", nx_file_dir_path)
    return nx_file_dir_path


def get_nx_log_file_dir_path():
    """get_nx_log_file_dir_path.

    Retrieve the log file dir path from the environment variable.

    This function checks the environment variable `_NX_LOG_FILE_DIR_PATH` to
    determine the path to the application's log file directory. If the variable
    is not set, a `ValueError` is raised.

    Returns:
        str: The log file dir path.

    Raises:
        ValueError: If the `_NX_LOG_FILE_DIR_PATH` environment variable is not
        defined.

    Notes:
        - The `_NX_LOG_FILE_DIR_PATH` variable must be set in the environment
          configuration file (e.g., `~/etc/environment`) for this function to
          work correctly.
        - This function is designed for environments where paths are configured
          via environment variables, such as containerized setups.
    """
    # Extract from env variable log file path (in container)
    nx_log_file_dir_path = os.environ.get("_NX_LOG_FILE_DIR_PATH")
    if nx_log_file_dir_path is None:
        logger.error(
            "Environment variable '_NX_LOG_FILE_DIR_PATH' is not set. "
            "Unable to retrieve nexus log file dir path."
        )
        raise ValueError(
            "_NX_LOG_FILE_DIR_PATH is None. Check content of ~/etc/environment."
        )
    logger.debug("Retrieved nexus log file dir path: %s", nx_log_file_dir_path)
    return nx_log_file_dir_path
