"""
This module defines a collection of constants and mappings used
throughout the application, particularly related to Nexus data files,
metadata, device schemas, and other configuration-related information.
These constants facilitate the operation of the system, ensuring
consistency, reducing the likelihood of errors, and enhancing
maintainability by avoiding the use of hard-coded values.
"""

import numpy as np
from h5py import string_dtype
from numpy import dtype

NOT_AVAILABLE_LABEL: str = "NotAvailable"
"""Label representing unavailable data."""

PRE_RUN_CPT_LABEL: str = "$pre-run-cpt"
"""Label for pre-run component placeholders."""

PRE_RUN_MD_LABEL: str = "$pre-run-md"
"""Label for pre-run metadata placeholders"""

NX_MD_KEY: str = "nexus_md"
"""The key used for Nexus metadata ("nexus_md")."""

DEVICE_MD_KEY: str = "device_md"
"""The key used for device metadata ("device_md")."""
NX_FILE_EXTENSION: str = ".nxs"
"""The file extension for Nexus files (".nxs")."""

CALLBACK_FILE_EXTENSION: str = ".json"
"""The file extension for callback files."""

NX_SCHEMA_MODEL_NAME_KEY: str = "nx_model"
"""Key for the Nexus schema model name."""

DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME: str = "nx_schema"
"""Attribute name for the Nexus schema in the device class"""

DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME: str = "nx_model"
"""
Attribute name for the Nexus schema in the device class.
"""

VALID_NXFIELD_DTYPES: list[str] = [
    "float32",
    "float64",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "str",
    "bool",
]
"""Valid datatypes that fields in the schema can be specified as."""

NX_DTYPE_MAP: dict[str, dtype] = {
    "float32": np.dtype("float32"),
    "float64": np.dtype("float64"),
    "int8": np.dtype("int8"),
    "int16": np.dtype("int16"),
    "int32": np.dtype("int32"),
    "int64": np.dtype("int64"),
    "uint8": np.dtype("uint8"),
    "uint16": np.dtype("uint16"),
    "uint32": np.dtype("uint32"),
    "uint64": np.dtype("uint64"),
    "char": string_dtype(encoding="utf-8"),
    "str": string_dtype(encoding="utf-8"),
    "bool": np.dtype("uint8"),
}
"""
A mapping of Nexus field data types to their corresponding numpy or h5py types.

These are all straightforward, apart from:
    - "char" maps to h5py.string_dtype(encoding="utf-8")
    - "bool" maps to np.uint8 (HDF5 does not support bool natively; store as uint8)
"""
