"""Utilities for validating arguments to methods with more pleasant errors."""

import os
from pathlib import Path


def validate_directory(path: str | Path, name: str) -> Path:
    """Validate that ``path`` exists, is a directory, and is writable.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to validate.

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
        raise ValueError(f"{name} does not exist: {path}.")

    if not p.is_dir():
        raise ValueError(f"{name} exists but is not a directory: {p}")

    if not os.access(str(p), os.W_OK):
        raise ValueError(f"{name} is not writable: {p}")

    return p
