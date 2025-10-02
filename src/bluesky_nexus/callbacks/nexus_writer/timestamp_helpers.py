"""Helpers for creating and managing timestamp datasets.

in NeXus HDF5 files.

This module provides functions to add special timestamp datasets to HDF5 groups,
typically representing timestamps related to events or descriptors in NeXus data.

Functions handle different data types (including object arrays and scalars),
apply appropriate UTF-8 encoding for strings, and assign NeXus-compliant
attributes like 'NX_class' and 'description'.

Main functions:
- add_special_timestamps: Creates datasets for specialized timestamp fields.
- add_events_timestamps: Adds 'events_timestamps' dataset if not already present,
  handling various data formats.
"""

import h5py  # type: ignore
import numpy as np

from bluesky_nexus.common.logging_utils import logger


def add_special_timestamps(
    key: str, timestamps_key: str, value: dict, group: h5py.Group
):
    """Create an HDF5 dataset for special timestamp fields.

    Field is created within the given group.

    Handles object and scalar numpy arrays by converting to suitable
    UTF-8 encoded strings or numeric arrays. Sets NeXus attributes like 'NX_class',
    'shape', and a description attribute referencing the source of timestamps.

    Parameters
    ----------
    key : str
        The base key name associated with the timestamps.
    timestamps_key : str
        The key in the value dict that contains the timestamp data.
    value : dict
        Dictionary containing the timestamp data and associated metadata.
    group : h5py.Group
        The HDF5 group to which the timestamp dataset will be added.
    """
    timestamps = value[timestamps_key]
    ds_key: str = key + "_timestamps"

    # If the numpy array is of dtype 'object':
    # This is a case when the data coming from events:
    #   - is a list of elements having different data types
    #   - is a list of strings
    #   - is just a string, in this case we deal with numpy array of ndim=0 (scalar)
    if timestamps.dtype == object:
        # Check if the numpy array is a scalar (ndim=0) or has more dimensions
        if timestamps.ndim == 0:
            # If it's a scalar, convert it to a 1D array with a single element
            timestamps = np.array(
                [timestamps.item()],
                dtype=object,
            )

        # Convert all elements to string (including numbers, None, etc.)
        timestamps = np.array(
            [str(item) if item is not None else "None" for item in timestamps],
            dtype=object,
        )

        # Apply variable-length UTF-8 encoding for the string
        dtype = h5py.string_dtype(encoding="utf-8")
        ds = group.create_dataset(ds_key, data=timestamps, dtype=dtype)
        # Assign attribute
        ds.attrs["NX_class"] = "NX_CHAR"

    # If the numpy array is NOT of dtype 'object':
    # This is a case when the data coming from events
    #   - is a list of floats, integers
    #   - is a float, integer
    else:
        # Check if the numpy array is a scalar (ndim=0) # or has more dimensions
        if timestamps.ndim == 0:
            # If it's a scalar, convert it to a 1D array with a single element
            timestamps = np.array([timestamps.item()], dtype=timestamps.dtype)

        ds = group.create_dataset(ds_key, data=timestamps, dtype=timestamps.dtype)

        # Assign attribute
        if "float64" == str(timestamps.dtype):
            ds.attrs["NX_class"] = "NX_FLOAT"
        elif "int64" == str(timestamps.dtype):
            ds.attrs["NX_class"] = "NX_INT"
        else:
            ds.attrs["NX_class"] = "NX_UNKNOWN"

    # Assign attributes
    ds.attrs["shape"] = list(timestamps.shape)

    src: str = timestamps_key.split("_")[0]
    ds.attrs["description"] = (
        f"Timestamps of the component: {key} extracted from the {src}"
    )

    # Log
    logger.debug(
        "New dataset for: %s, dtype: %s, key: %s, group: %s, value: %s",
        timestamps_key.replace("_", " "),
        ds.dtype,
        ds_key,
        group.name,
        timestamps,
    )


def add_events_timestamps(key: str, value: dict, group: h5py.Group):
    """Create an 'events_timestamps' dataset.

    Dataset is created within the group if it does not exist.

    Supports various data types (including object arrays and scalars), converts
    strings to UTF-8 encoded datasets, and sets NeXus attributes such as 'NX_class',
    'shape', and a description.

    Parameters
    ----------
    key : str
        The base key name associated with the events.
    value : dict
        Dictionary containing the 'events_timestamps' data and metadata.
    group : h5py.Group
        The HDF5 group to which the 'events_timestamps' dataset will be added.
    """
    # Check if the dataset already exists
    if "events_timestamps" in group:
        return

    # Create dataset for 'events_timestamps'
    timestamps = value["events_timestamps"]
    ds_key = "events_timestamps"

    # If the numpy array is of dtype 'object':
    # This is a case when the data coming from events is:
    # - a list of elements having different data types
    # - a list of strings
    # - just a string, in this case we deal with numpy array of ndim=0 (scalar)

    if timestamps.dtype == object:
        # Check if the numpy array is a scalar (ndim=0) or has more dimensions
        if timestamps.ndim == 0:
            # If it's a scalar, convert it to a 1D array with a single element
            timestamps = np.array([timestamps.item()], dtype=object)

        # Convert all elements to string (including numbers, None, etc.)
        timestamps = np.array(
            [(str(item) if item is not None else "None") for item in timestamps],
            dtype=object,
        )

        # Apply variable-length UTF-8 encoding for the string
        dtype_ = h5py.string_dtype(encoding="utf-8")
        ds = group.create_dataset(ds_key, data=timestamps, dtype=dtype_)
        # Assign attribute
        ds.attrs["NX_class"] = "NX_CHAR"

    # If the numpy array is NOT of dtype 'object':
    # This is a case when the data coming from events is:
    # - a list of floats, integers
    # - a float, integer
    else:
        # Check if the numpy array is a scalar (ndim=0) or has more dimensions
        if timestamps.ndim == 0:
            # If it's a scalar, convert it to a 1D array with a single element
            timestamps = np.array([timestamps.item()], dtype=timestamps.dtype)

        ds = group.create_dataset(ds_key, data=timestamps, dtype=timestamps.dtype)
        # Assign attributes
        if "float64" == str(timestamps.dtype):
            ds.attrs["NX_class"] = "NX_FLOAT"
        elif "int64" == str(timestamps.dtype):
            ds.attrs["NX_class"] = "NX_INT"
        else:
            ds.attrs["NX_class"] = "NX_UNKNOWN"

    ds.attrs["shape"] = list(timestamps.shape)
    ds.attrs["description"] = "Timestamps of the events"
    logger.debug(
        "New dataset for events_timestamps: dtype: %s, key: %s, group: %s, value: %s",
        ds.dtype,
        key,
        group.name,
        timestamps,
    )
