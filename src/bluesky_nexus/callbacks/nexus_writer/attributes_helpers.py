"""attributes_helpers.py.

Module for adding attributes to HDF5 datasets or groups.

This module provides utility functions to apply attributes to HDF5
datasets or groups (`h5py.Dataset` or `h5py.Group`) in NeXus files,
using metadata defined in a dictionary. Attributes are type-enforced
according to NeXus conventions and mapped to appropriate HDF5-compatible dtypes.

Functions:
----------
- add_attributes: Apply attributes with validated and mapped dtypes.

Dependencies:
-------------
- h5py
- numpy
- bluesky_nexus_const.NX_DTYPE_MAP: A mapping from string-based dtype
  descriptors to NumPy/HDF5 dtypes.

Typical usage involves schema-based attribute metadata, such as:

    {
        "units": {"value": "keV", "dtype": "str"},
        "flag": {"value": True, "dtype": "bool"}
    }

This module is typically used during NeXus file generation or schema-driven
HDF5 writing for scientific experiments.
"""

from typing import Any, Union

import h5py  # type: ignore
import numpy as np

from bluesky_nexus.bluesky_nexus_const import NX_DTYPE_MAP


def add_attributes(target: Union[h5py.Dataset, h5py.Group], attributes: dict) -> None:
    """add_attributes.

    Adds attributes to an HDF5 dataset or group, enforcing dtype if specified.

    Parameters:
    - target Union[h5py.Dataset, h5py.Group]: The dataset or group to which
    attributes should be added.
    - attributes (dict): A dictionary of attributes to add, each with 'value' and
    'dtype' keys.
    """
    for attr_name, attr_data in attributes.items():
        value: Any = attr_data[
            "value"
        ]  # Mandatory, guaranteed by NXfieldModelForAttribute
        dtype_str: str = attr_data["dtype"]  # Expected as a string, facultative for
        # post-run placeholders otherwise mandatory

        if dtype_str not in NX_DTYPE_MAP:
            raise ValueError(
                f"Invalid dtype: {dtype_str} detected while "
                f"processing {target.name}.{attr_name}."
            )

        try:
            dtype = NX_DTYPE_MAP[dtype_str]

            # Handle strings explicitly
            if dtype in {h5py.string_dtype(encoding="utf-8")}:
                if isinstance(value, str):
                    value = np.array(
                        value, dtype=dtype
                    )  # Convert scalar string to numpy array
                elif isinstance(value, (list, tuple, np.ndarray)):
                    value = np.array(
                        value, dtype=dtype
                    )  # Convert list of strings to numpy array
                else:
                    raise TypeError(
                        f"Unexpected type {type(value)} for "
                        f"string attribute {attr_name}"
                    )

            # Handle booleans explicitly
            elif dtype == np.uint8 and isinstance(value, (bool, np.bool_)):
                value = np.uint8(value)  # Convert single bool to uint8

            # Convert numpy arrays correctly
            elif isinstance(value, np.ndarray):
                value = value.astype(dtype)

            # Convert scalar values correctly
            else:
                value = np.array(value, dtype=dtype)

            # Save the attribute
            target.attrs[attr_name] = value

        except Exception as e:
            raise TypeError(
                f"Failed to convert {value} to dtype {dtype_str}: {e}"
            ) from e
