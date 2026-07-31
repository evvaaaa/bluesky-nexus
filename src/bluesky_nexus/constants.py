"""
This module defines a collection of constants and mappings used
throughout the application, particularly related to Nexus data files,
metadata, device schemas, and other configuration-related information.
These constants facilitate the operation of the system, ensuring
consistency, reducing the likelihood of errors, and enhancing
maintainability by avoiding the use of hard-coded values.
"""

NX_FILE_EXTENSION: str = ".nxs"
"""The file extension for Nexus files (".nxs")."""

DEVICE_SCHEMA_NAME_KEY: str = "<name>"
"""the key in the device schema to swap with the object name."""

DEFAULT_PLAN_NAME = "NO-PLAN-NAME"
"""Plan name to use for generating the nexus file name if "plan_name" or
"plan_abbreviation are not in the run start."""
