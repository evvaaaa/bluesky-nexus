"""attrs_helpers.py.

Utility module for dynamically adding attributes to HDF5 datasets.

This module provides functionality to attach a variety of attribute types
(e.g., strings, booleans, numerics, arrays, and dictionaries) to an HDF5
dataset using h5py.py, inferring and applying the appropriate dtype automatically.

Key Function:
-------------
- add_attrs(dataset, attrs): Attach metadata to an h5py.Dataset using
  flexible type handling.

Supported Attribute Types:
---------------------------
- Scalar values: str, bool, int, float
- Arrays/lists/tuples of numbers, booleans, or strings
- Dictionaries (serialized to JSON strings)

The function enforces consistency in dtype representation, ensuring proper
NeXus-compliant and HDF5-compatible storage.
"""

import json

import h5py  # type: ignore
import numpy as np


def add_attrs(dataset: h5py.Dataset, attrs: dict) -> None:
    """add_attrs.

    Adds attributes to an h5py dataset, automatically determining
    their type.

    Parameters:
    - dataset (h5py.Dataset): The dataset to which attributes should
    be added.
    - attrs (dict): A dictionary where keys are attribute names and
    values are attribute values.
    """
    for key, value in attrs.items():
        # Automatically determine the type and convert accordingly

        # Handle dictionaries
        if isinstance(value, dict):
            json_str = json.dumps(value)  # Convert dictionary to JSON string
            dtype = h5py.string_dtype(encoding="utf-8")  # Ensure UTF-8 encoding
            dataset.attrs[key] = np.array(json_str, dtype=dtype)
            continue

        # Handle strings
        if isinstance(value, str):
            dtype = h5py.string_dtype(encoding="utf-8")  # Ensure UTF-8 encoding
            # Convert scalar string to numpy array
            dataset.attrs[key] = np.array(value, dtype=dtype)
            continue

        # Handle basic types
        if isinstance(value, bool):
            dataset.attrs[key] = np.bool_(value)  # Store as a NumPy boolean
            continue

        if isinstance(value, (int, np.integer)):
            # Store as int64 (safe for large numbers)
            dataset.attrs[key] = np.int64(value)
            continue

        if isinstance(value, (float, np.floating)):
            # Store as float64 for precision
            dataset.attrs[key] = np.float64(value)
            continue

        # Handle sequences and arrays
        if isinstance(value, (list, tuple, np.ndarray)):
            # Convert sequences or arrays to numpy array for consistent storage
            arr = np.array(value)
            kind = arr.dtype.kind

            if kind in {"i", "u"}:  # Integer types
                dataset.attrs[key] = arr.astype(np.int64)
            elif kind == "f":  # Floating point types
                dataset.attrs[key] = arr.astype(np.float64)
            elif kind == "b":  # Boolean array
                dataset.attrs[key] = arr.astype(np.bool_)
            elif kind in {"U", "O"}:  # String
                dtype = h5py.special_dtype(vlen=str)
                dataset.attrs[key] = np.array(arr, dtype=dtype)
            else:
                raise ValueError(
                    f"Unsupported array data type for attribute '{key}': {arr.dtype}"
                )
            continue

        # Unsupported type
        raise ValueError(f"Unsupported attribute type for '{key}': {type(value)}")
