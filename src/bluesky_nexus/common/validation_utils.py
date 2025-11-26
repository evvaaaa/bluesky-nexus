"""Utilities for validating filesystem paths.

This module provides helper functions to ensure that user-specified
directories are valid before starting the data-writing service.

Currently, the module exposes:

validate_directory(path, name)     Normalize and validate a directory
path, raising a ValueError if the     path is missing, not a directory,
or not writable.
"""

import os
from pathlib import Path


def validate_directory(path: str | Path, name: str) -> Path:
    """Validate that ``path`` exists, is a directory, and is writable.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to validate.
    name : str
        Human-readable name of the directory (e.g. "NeXus output directory").

    Returns
    -------
    pathlib.Path
        Normalized and validated path.

    Raises
    ------
    ValueError
        If the directory does not exist, is not a directory,
        or is not writable.
    """
    p = Path(path)

    if not p.exists():
        raise ValueError(f"{name} does not exist: {p}")

    if not p.is_dir():
        raise ValueError(f"{name} exists but is not a directory: {p}")

    if not os.access(str(p), os.W_OK):
        raise ValueError(f"{name} is not writable: {p}")

    return p
