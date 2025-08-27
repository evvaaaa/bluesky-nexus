"""dataset_helpers.py.

Dataset creation utilities for HDF5 files using h5py.

This module provides a helper function for safely creating HDF5 datasets
inside a given group. It supports a wide variety of input types—such as
NumPy arrays, scalars, strings, lists, and dictionaries—by applying
appropriate data conversion and encoding strategies.

Key Features
------------
- Automatic type inference and safe coercion for mixed-type and scalar values.
- Special handling for strings and dictionaries (e.g., JSON serialization).
- UTF-8 encoding for string values and string arrays.
- Extensive debug logging for tracking dataset creation and failures.

Function
--------
- create_dataset_with_value(key, val, dtype, group): Creates a dataset with
  safe dtype enforcement and detailed error logging.
"""

import json
from typing import Any, Optional

import h5py  # type: ignore
import numpy as np

from bluesky_nexus.common.logging_utils import logger


def create_dataset_with_value(
    key: str, val: Any, dtype: Any, group: h5py.Group
) -> Optional[h5py.Dataset]:
    """Create an HDF5 dataset in the given group.

    Application of type-safe conversion.

    Handles scalar values, lists, strings, NumPy arrays, and dictionaries by
    coercing them into compatible HDF5 data formats. Provides UTF-8 encoding for
    strings and JSON serialization for dictionaries. Logs debug messages for
    all dataset creations and warnings for unsupported types.

    Parameters
    ----------
    key : str
        The name of the dataset to create.
    val : Any
        The value to store. Supported types: str, int, float, bool, list, dict,
        np.ndarray.
    dtype : Any
        Desired data type. May be overridden for string and object handling.
    group : h5py.Group
        The HDF5 group in which the dataset is created.

    Returns
    -------
    h5py.Dataset or None
        The created dataset, or None if the value type is unsupported.

    Notes
    -----
    - Strings and string arrays are encoded as UTF-8.
    - Dictionaries are serialized to JSON before storage.
    - Logs errors for unsupported types without raising exceptions.
    """
    ds = None  # default

    # If val is a numpy array
    if isinstance(val, np.ndarray):

        # If the numpy array is of dtype 'object':
        # This is a case when the data coming from events or descriptor is:
        #  - a list of elements having different data types
        #  - a list of strings
        #  - a string, in this case we deal with numpy array of ndim=0 (scalar)

        if val.dtype == object:

            # Check if the numpy array is a scalar (ndim=0) or has more dimensions
            if val.ndim == 0:
                # If it's a scalar, convert it to a 1D array with a single element
                val = np.array([val.item()], dtype=object)

            # Convert all elements to string (including numbers, None, etc.)
            val = np.array(
                [str(item) if item is not None else "None" for item in val],
                dtype=object,
            )

            # Apply variable-length UTF-8 encoding for the string
            dtype = h5py.string_dtype(encoding="utf-8")
            ds = group.create_dataset(key, data=val, dtype=dtype)
            logger.debug(
                "New dataset: encoding: utf8, dtype: %s, key: %s,"
                " group: %s, value: %s",
                dtype,
                key,
                group.name,
                val,
            )

        # If the numpy array is NOT of dtype 'object':
        # This is a case when the data coming from events or descriptor is:
        #  - a list of floats, integers, booleans
        #  - a float, integer, boolean
        else:
            # Check if the numpy array is a scalar
            # (ndim=0) or has more dimensions
            if val.ndim == 0:
                # If it's a scalar, convert it
                # to a 1D array with a single element
                val = np.array([val.item()], dtype=dtype)

            ds = group.create_dataset(key, data=val, dtype=dtype)
            logger.debug(
                "New dataset: dtype: %s, key: %s, group: %s, value: %s",
                dtype,
                key,
                group.name,
                val,
            )

    # If val is an instance of str
    elif isinstance(val, str):

        # Convert it to a 1D array with a single element
        val = np.array([val], dtype=object)

        # Apply variable-length UTF-8 encoding for the string
        dtype = h5py.string_dtype(encoding="utf-8")

        # Create dataset
        ds = group.create_dataset(key, data=val, dtype=dtype)
        logger.debug(
            "New dataset: encoding: utf8, dtype: %s, key: %s, group: %s, value: %s",
            dtype,
            key,
            group.name,
            val,
        )

    # If val is an instance of int, double, bool
    elif isinstance(val, (int, float, bool)):

        # Convert it to a 1D array with a single element
        val = np.array([val])

        # Create dataset for 'value'
        ds = group.create_dataset(key, data=val, dtype=dtype)
        logger.debug(
            "New dataset: dtype: %s, key: %s, group: %s, value: %s",
            dtype,
            key,
            group.name,
            val,
        )

    elif isinstance(val, list):

        # There is a string in the list
        if any(isinstance(v, (str, np.str_)) for v in val):
            # Convert all elements to string (including numbers, None, etc.)
            val = np.array(
                [(str(item) if item is not None else "None") for item in val],
                dtype=object,
            )

            # Apply variable-length UTF-8 encoding for the string
            dtype = h5py.string_dtype(encoding="utf-8")
            ds = group.create_dataset(key, data=val, dtype=dtype)
            logger.debug(
                "New dataset: encoding: utf8, dtype: %s, key: %s,"
                " group: %s, value: %s",
                dtype,
                key,
                group.name,
                val,
            )
        else:
            # There is no string in the list
            val = np.array(val)
            ds = group.create_dataset(key, data=val, dtype=dtype)
            logger.debug(
                "New dataset: dtype: %s, key: %s, group: %s, value: %s",
                dtype,
                key,
                group.name,
                val,
            )

    elif isinstance(val, dict):

        # Convert dictionary to JSON string
        val = json.dumps(val)

        # Convert it to a 1D array with a single element
        val = np.array([val], dtype=object)

        # Ensure UTF-8 encoding
        dtype = h5py.string_dtype(encoding="utf-8")

        ds = group.create_dataset(key, data=val, dtype=dtype)
        logger.debug(
            "New dataset: encoding: utf8, dtype: %s, key: %s, group: %s, value: %s",
            dtype,
            key,
            group.name,
            val,
        )
    else:
        # Unsupported instance of value["value"]
        logger.error(
            "Unsupported case detected. Please contact developer,"
            " dtype: %s, key: %s, group: %s, value: %s",
            dtype,
            key,
            group.name,
            val,
        )
        return ds

    logger.debug(
        "New dataset: dtype: %s, key: %s, group: %s, value: %s",
        dtype,
        key,
        group.name,
        val,
    )
    return ds
