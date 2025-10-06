"""Module bluesky_nexus_const.

This module defines a collection of constants and mappings used
throughout the application, particularly related to Nexus data files,
metadata, device schemas, and other configuration-related information.
These constants facilitate the operation of the system, ensuring
consistency, reducing the likelihood of errors, and enhancing
maintainability by avoiding the use of hard-coded values.

Constants:

    NOT_AVAILABLE_LABEL (str): Label representing unavailable data
        ("NotAvailable").
    PRE_RUN_CPT_LABEL (str): Label for pre-run component placeholders
        ("$pre-run-cpt").
    PRE_RUN_MD_LABEL (str): Label for pre-run metadata placeholders
        ("$pre-run-md").
    NX_MD_KEY (str): The key used for Nexus metadata ("nexus_md").
    DEVICE_MD_KEY (str): The key used for device metadata ("device_md").
    NX_FILE_EXTENSION (str): The file extension for Nexus files (".nxs").
    CALLBACK_FILE_EXTENSION (str): The file extension for callback files
        (".json").
    NX_SCHEMA_MODEL_NAME_KEY (str): Key for the Nexus schema model name
        ("nx_model").
    DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME (str): Attribute name for the Nexus
        schema in the device class ("nx_schema").
    DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME (str): Attribute name for the
        Nexus model in the device instance ("nx_model").
    DEFAULT_NX_LOG_FORMAT (str): The default log format used by the logger.

Valid Data Types for Nexus Fields:

    VALID_NXFIELD_DTYPES (list): List of valid data types for Nexus fields,
        including numeric types (e.g., float32, int32), unsigned integers
        (e.g., uint8, uint16), and string types ("char", "str").

Mappings:

    NX_DTYPE_MAP (dict): A dictionary mapping valid Nexus field data types to
        their corresponding numpy or h5py types. This mapping is used for
        type conversion between Nexus data and the internal representation:
            - "float32" maps to np.float32
            - "float64" maps to np.float64
            - "int8" maps to np.int8
            - "int16" maps to np.int16
            - "int32" maps to np.int32
            - "int64" maps to np.int64
            - "uint8" maps to np.uint8
            - "uint16" maps to np.uint16
            - "uint32" maps to np.uint32
            - "uint64" maps to np.uint64
            - "char" maps to h5py.string_dtype(encoding="utf-8")
            - "str" maps to h5py.string_dtype(encoding="utf-8")
            - "bool" maps to np.uint8 (HDF5 does not support bool natively;
              store as uint8)
"""

from typing import Dict

import numpy as np
from h5py import string_dtype  # type: ignore
from numpy import dtype

NOT_AVAILABLE_LABEL: str = "NotAvailable"
PRE_RUN_CPT_LABEL: str = "$pre-run-cpt"
PRE_RUN_MD_LABEL: str = "$pre-run-md"
NX_MD_KEY: str = "nexus_md"
DEVICE_MD_KEY: str = "device_md"
NX_FILE_EXTENSION: str = ".nxs"
CALLBACK_FILE_EXTENSION: str = ".json"
NX_SCHEMA_MODEL_NAME_KEY: str = "nx_model"
DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME: str = "nx_schema"
DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME: str = "nx_model"
DEFAULT_NX_LOG_FORMAT: str = (
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s  %(message)s"
)

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

NX_DTYPE_MAP: Dict[str, dtype] = {
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
    "bool": np.dtype("uint8"),  # HDF5 does not support bool natively, store as uint8
}
