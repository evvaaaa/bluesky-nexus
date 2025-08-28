"""Module for Creating and Writing NeXus Files.

This module contains functions for generating NeXus files in the HDF5
format using a dictionary-based approach. The functions allow the
creation of a hierarchical structure within the NeXus file, with
special handling for specific NeXus groups such as 'instrument' and
'run_info'. The module supports various types of data, including
simple values, lists, and more complex nested structures.

Functions provided in this module include:

- `extract_run_info(start: dict, stop: dict) -> dict`: Extracts
  relevant information from the start and stop documents and returns
  a dictionary containing the relevant data.
- `create_nexus_file(file_path, data_dict)`: Creates a NeXus file at
  the specified file path using the provided data dictionary,
  handling groups and datasets based on the NeXus standard.
- `add_group_or_field(group, data)`: Recursively adds groups or
  datasets to a NeXus file based on the provided data, supporting
  nested structures and various data types.
- `write_collection(group, data: dict)`: Recursively writes a
  collection of data (nested dictionaries, lists, and primitive
  values) to a given group in the NeXus file, handling different data
  types appropriately.

The module ensures that valid data types are used for fields and
datasets, and it validates input to avoid errors in the NeXus file
structure. It is intended for use cases where NeXus data needs to be
programmatically created and stored in HDF5 format, with support for
complex data types and nested hierarchies.

Example Usage:

    # Example of using the module to create a NeXus file
    data = {
        "instrument": {"mono": {"NX_class": "NXmonochromator",
                               "value": 123.4}},
        "run_info": {"start_time": "2023-12-01T12:00:00"},
    }
    create_nexus_file("example.nxs", data)

Notes:
    - The module expects the provided data dictionary to be
      well-structured according to the NeXus format.
    - Special handling for fields like 'events_cpt_timestamps' and
      'events_timestamps' is included.
    - Error handling is in place to manage invalid data types and
      unsupported structures.
"""

import copy
import os
from collections import deque
from functools import partial
from typing import Any, Deque, Dict

import h5py  # type: ignore
import numpy as np
from bluesky.callbacks.core import CollectThenCompute

from bluesky_nexus.bluesky_nexus_const import (
    DEVICE_MD_KEY,
    NX_FILE_EXTENSION,
    NX_MD_KEY,
)
from bluesky_nexus.callbacks.nexus_writer.group_helpers import add_group_or_field
from bluesky_nexus.callbacks.nexus_writer.placeholder_helpers import (
    replace_func,
    replace_values,
)
from bluesky_nexus.common.decorator_utils import measure_time
from bluesky_nexus.common.logging_utils import logger


class NexusWriter(CollectThenCompute):
    """NexusWriter.

    This class handles the extraction of relevant metadata from the documents
    (start, stop, event, and descriptor documents), processes it,
    and generates a NeXus file in HDF5 format. It is designed to work within
    a data collection pipeline, that interacts with a RunEngine and manages
    data collection, processing, and file writing.

    Inherits from:
        CollectThenCompute

    Parameters:
        nx_file_dir_path (str): Path to the directory where NeXus files
            will be saved.
        cpt_name_delimiter (str): Delimiter for device component
            names applied in bluesky documents. Per default: "_", valid
            for ophyd devices.

    Public Methods:
        - __call__(name, doc): Handles incoming documents from the RunEngine,
        processing them based on their type ('start', 'stop', etc.).
        - create_nx_file_path(dir_path, file_name): Constructs and validates
            the NeXus file path.
        - compute(): Entry point to trigger NeXus file generation.
        - generate_nexus_file(): Extracts metadata and writes the NeXus file.
    """

    def __init__(self, nx_file_dir_path: str, cpt_name_delimiter: str = "_") -> None:
        """Init.

        Initialize with NeXus file path and component name delimiter.
        """
        super().__init__()  # Initialize the parent class
        self.nx_file_dir_path = nx_file_dir_path
        self.cpt_name_delimiter = cpt_name_delimiter

    # pylint: disable=signature-differs
    def __call__(self, name: str, doc: dict) -> None:
        """Call.

        Handle documents from the RunEngine and delegate them to
        the appropriate methods based on the document type.

        Parameters:
            name (str): The type of the document (e.g., 'start', 'stop',
                'descriptor', 'event').
            doc (dict): The content of the document, which is passed to the
                corresponding method for processing (e.g., start document,
                event data, etc.).

        Notes:
            - The method ensures that documents are processed in the correct
            sequence (start -> descriptor -> event -> stop).
            - This method delegates the responsibility of handling each
                document type to specific class methods.
        """
        if name == "start":
            self.start(doc)
        elif name == "descriptor":
            self.descriptor(doc)
        elif name == "event":
            self.event(doc)
        elif name == "stop":
            self.stop(doc)

    def create_nx_file_path(self, dir_path: str, file_name: str) -> str:
        """Create nx_file_path.

        Creates a valid file path for the NeXus file, ensuring the directory
        exists and the file name adheres to the expected format.

        Parameters:
            dir_path (str): The directory path where the NeXus file will
            be saved. file_name (str): The desired name of the NeXus file.
            If None or empty, a name will be auto-generated using the UID
            from the start document.

        Returns:
            str: The complete file path for the NeXus file.

        Raises:
            ValueError: If the provided directory path is not a
            valid directory.

        Notes:
            - If the file name is not provided, it defaults to a generated
            name based on the UID in the start document with the proper NeXus
            file extension.
            - If the file name contains "{uid}", it is replaced with the UID
            from the start document.
            - The file name will always have the NeXus file extension appended
            if not already present.
        """
        # Check if 'dir_path' is pointing to existing directory
        if not os.path.isdir(dir_path):
            raise ValueError(
                f"Nexus dir path {dir_path} is not pointing to a directory."
            )

        # Check if 'file_name' is not None or not empty string
        if file_name is None or not file_name.strip():
            file_name = self._start_doc["uid"]
            file_name = file_name + NX_FILE_EXTENSION
            logger.warning(
                "Nexus file name not defined by the user. Nexus file name "
                "automatically generated to '%s'",
                file_name,
            )

        # Add extension to file name
        if not file_name.endswith(NX_FILE_EXTENSION):
            file_name = file_name + NX_FILE_EXTENSION

        # Add uid to file name if necessary
        if "{uid}" in file_name:
            file_name = file_name.format(uid=self._start_doc["uid"])

        # Define nexus file path
        file_path: str = os.path.join(dir_path, file_name)

        return file_path

    def compute(self) -> None:
        """Compute.

        Triggers the process of generating the NeXus file by calling
        `generate_nexus_file()`.

        This method acts as a simple entry point for processing the
        metadata and writing the NeXus file.
        """
        self.generate_nexus_file()

    @measure_time
    def generate_nexus_file(self) -> None:
        """Generate nexus file.

        Processes the NeXus metadata and writes a NeXus file based on
        the start, stop, event, and descriptor documents.

        The workflow includes:
            1. Verifying the presence of necessary metadata in the start
            document.
            2. Retrieving configuration from the environment, such as
            the NeXus directory path.
            3. Generating the NeXus file path using the directory and file
            name.
            4. Extracting run information from the start and stop documents.
            5. Safely creating a deepcopy of the start document
            for processing.
            6. Handling placeholders in the metadata using event
            and descriptor data.
            7. Combining instrument metadata with run information.
            8. Writing the NeXus file with the combined data.

        Raises:
            Exception: If an error occurs during the deepcopy of
            the start document.

        Notes:
            - If required metadata is missing from the start document,
            an error message is logged.
            - The method processes placeholders within the NeXus
            metadata using the associated events and descriptors.
        """

        def collect_descriptor_keys(descriptors: deque) -> set:
            """Find out devices/objects of a run.

            Collects all unique keys from 'configuration' and
            'object_keys' in a deque of Bluesky descriptors.

            Args:
                descriptors (deque): deque containing descriptor dictionaries

            Returns:
                set: a set of unique keys found under 'configuration' and 'object_keys'
            """
            keys_set = set()

            for descriptor in descriptors:
                # Collect keys under 'configuration'
                configuration = descriptor.get("configuration", {})
                keys_set.update(configuration.keys())

                # Collect keys under 'object_keys'
                object_keys = descriptor.get("object_keys", {})
                keys_set.update(object_keys.keys())

            return keys_set

        def filter_start_doc(
            start_doc_cpy: dict, keys_set: set, delimiter: str = "_"
        ) -> dict:
            """Remove device names not taking part in run.

            Filters 'device_md' and 'nexus_md' in start_doc_cpy,
            keeping only those entries whose keys either:
            1. exactly match a key in keys_set, or
            2. are a prefix of some key in keys_set, followed by the delimiter.

            Args:
                start_doc_cpy (dict): dictionary with at least
                    'device_md' and 'nexus_md'
                keys_set (set): set of valid keys from descriptors
                delimiter (str): string that separates a prefix from
                    the rest of a key (default "_")

            Returns:
                dict: the filtered start_doc_cpy, with invalid devices removed
            """

            def is_valid_key(key: str) -> bool:
                # exact match
                if key in keys_set:
                    return True
                # prefix match with delimiter
                for k in keys_set:
                    if k.startswith(f"{key}{delimiter}"):
                        return True
                return False

            for section in [DEVICE_MD_KEY, NX_MD_KEY]:
                if section in start_doc_cpy and isinstance(
                    start_doc_cpy[section], dict
                ):
                    keys_to_remove = [
                        k for k in start_doc_cpy[section].keys() if not is_valid_key(k)
                    ]
                    for k in keys_to_remove:
                        del start_doc_cpy[section][k]

            return start_doc_cpy

        # Check if NEXUS_MD_KEY is contained in the start document
        if NX_MD_KEY not in self._start_doc:
            logger.error(
                "The start document does not contain '%s' dictionary.", NX_MD_KEY
            )
            return

        # Define nexus file dir path
        nx_dir_path: str = self.nx_file_dir_path

        # Retrieve nexus file name from start doc
        nx_file_name: str = self._start_doc.get("nx_file_name", None)

        # Create nexus file path
        nx_file_path: str = self.create_nx_file_path(nx_dir_path, nx_file_name)

        # Copy the start document to be able to modify it.
        # Reason: Documents are immutable.
        try:
            start_doc_cpy = copy.deepcopy(self._start_doc)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Error during deepcopy of the start document: '%s'", e)
            return

        ###  --- Clean  start_doc_cpy from device names not used in the plan ---
        # Collect from all descriptors unique keys of 'configuration' and 'object_keys'
        keys_set: set = collect_descriptor_keys(self._descriptors)
        # Remove under NX_MD_KEY: str = 'nexus_md' and DEVICE_MD_KEY: str = 'device_md'
        # contained in the start_doc_cpy all the device names
        # that are not used in the plan. They are not listed in the descriptors.
        delimiter: str = self.cpt_name_delimiter
        start_doc_cpy = filter_start_doc(start_doc_cpy, keys_set, delimiter)
        ###  --- End of Clean  start_doc_cpy from device names not used in the plan ---

        # Create 'run_info' dict by extraction of data from the
        # start and stop document
        run_info: dict = extract_run_info(start_doc_cpy, self._stop_doc)

        # Define a dict "data" that is to be passed to 'create_nexus_file()'
        data: dict = {"run_info": run_info}

        # If there is NX_MD_KEY in the start_doc_cpy
        if start_doc_cpy[NX_MD_KEY]:
            # Process the placeholders of the nexus_md applying
            # events and descriptors
            process_nexus_md(
                start_doc_cpy[NX_MD_KEY],
                self._descriptors,
                self._events,
                delimiter=self.cpt_name_delimiter,
            )

            # Update the dict data with instrument_data
            instrument_data: dict = start_doc_cpy[NX_MD_KEY]
            data.update({"instrument": instrument_data})

        # Create nexus file from the data
        create_nexus_file(nx_file_path, data)


# Define processing of the nexus md
def process_nexus_md(
    nexus_md: dict, descriptors: Deque, events: Deque, delimiter="_"
) -> None:
    """Process Nexus metadata.

    Replace `$post-run` placeholders with actual data.

    This function traverses the Nexus metadata dictionary and replaces any
    `$post-run:<component>` placeholders with actual values from the corresponding
    `descriptors` and `events`. The replacement logic is delegated to
    `process_post_run`.

    Parameters
    ----------
    nexus_md : dict
        The Nexus metadata dictionary to process. This typically represents
        a hierarchical structure containing measurement metadata with placeholders.
    descriptors : Deque
        A deque of descriptor documents from the Bluesky run. These contain metadata
        about the data streams collected.
    events : Deque
        A deque of event documents from the Bluesky run. These contain the actual
        measured data values.
    delimiter : str, optional
        The delimiter used to join the device name and component name. Default is "_".

    Raises
    ------
    ValueError
        If any of the input containers (`nexus_md`, `descriptors`, or `events`)
        is empty.
    """
    if not nexus_md:
        raise ValueError("The dict 'nexus_md' is empty")
    if not descriptors:
        raise ValueError("The deque 'descriptors' is empty")
    if not events:
        raise ValueError("The deque 'events' is empty")

    # Perform post-run placeholder resolution
    process_post_run(nexus_md, descriptors, events, delimiter)


def process_post_run(nexus_md, descriptors, events, delimiter) -> None:
    """Replace `$post-run` placeholders in Nexus metadata.

    Replace `$post-run` placeholders in Nexus metadata using event and descriptor data.

    Iterates through each device in the Nexus metadata and replaces any placeholder
    values matching the pattern `$post-run:<component>` using the provided
    `descriptors` and `events`. The replacement function is partially applied
    with the current context to simplify traversal.

    Parameters
    ----------
    nexus_md : dict
        The Nexus metadata dictionary to be modified in place.
    descriptors : Deque
        A deque of descriptor documents containing metadata and configuration info.
    events : Deque
        A deque of event documents containing measured data.
    delimiter : str
        The delimiter used to concatenate device and component names (e.g., "dev_cpt").
    """
    for dev_name in nexus_md.keys():
        replacer = partial(
            replace_func,
            descriptors=descriptors,
            events=events,
            delimiter=delimiter,
        )
        nexus_md[dev_name] = replace_values(dev_name, nexus_md[dev_name], replacer)


# Define extraction of run info
def extract_run_info(start: dict, stop: dict) -> dict:
    """Extract run info.

    Extract relevant information from the 'start' and 'stop' documents and
    return a dictionary with the extracted data.

    Args:
        start (dict): A dictionary representing the start document
            containing metadata for a run.
        stop (dict): A dictionary representing the stop document
            containing metadata for a run.

    Returns:
        dict: A dictionary with two keys, 'start' and 'stop', each
            containing the relevant data. The 'start' key will include data
            from the start document, excluding the 'nexus_md' and
            'device_md' keys. The 'stop' key will include the entire stop
            document.

    Notes:
        - The 'nexus_md' and 'device_md' keys are intentionally excluded
        from the 'start' document in the resulting dictionary.
    """
    start_label: str = "start"
    stop_label: str = "stop"

    # Define result dictionary
    result: dict = {start_label: {}, stop_label: {}}

    # Insert into the 'result[start_label]' dictionary the data
    # from the start document but not 'nexus_md'
    for key in start.keys():
        if NX_MD_KEY == key:
            # Do not add subdictionary of the key 'nexus_md'.
            continue
        result[start_label][key] = start[key]

    # Insert into the 'result[stop_label]' dictionary all
    # the data from the stop document
    result[stop_label] = stop

    # Return the result
    return result


def create_nexus_file(file_path: str, data_dict: Dict[str, Any]) -> None:
    """Create nexus file.

    Creates a NeXus file at the specified file path using the provided data
    dictionary.

    Parameters:
        file_path (str): The path where the NeXus file will be created.
        data_dict (dict): A dictionary containing the data to populate the
            NeXus file. Keys represent group or dataset names, and values
            represent their corresponding data or attributes. Special keys
            like "instrument" or "run_info" are treated as specific NeXus
            groups.

    Raises:
        ValueError: If invalid data types are detected for certain groups
            or fields.

    Example:
        data = {
            "instrument": {
                "mono": {"NX_class": "NXmonochromator", "value": 123.4}
            },
            "run_info": {"start_time": "2023-12-01T12:00:00"},
        }
        create_nexus_file("example.nxs", data)
    """
    with h5py.File(file_path, "w") as f:
        # Create file level attribute
        f.attrs["default"] = "entry"

        # Create the NXentry group
        entry = f.create_group("entry")
        entry.attrs["NX_class"] = "NXentry"
        entry.attrs["Application name"] = "bluesky_nexus"
        entry.attrs["Content"] = "'NXinstrument' group and 'NXcollection' group"

        for key, value in data_dict.items():
            # Create instrument group under 'entry' group
            if "instrument" == key:
                # Create instrument group
                instrument_group = entry.create_group(key)
                # Add attribute
                instrument_group.attrs["NX_class"] = "NXinstrument"
                instrument_group.attrs["description"] = (
                    "Instruments involved in the bluesky plan"
                )

                # Add group or field to instrument_group
                add_group_or_field(instrument_group, value)

            # Create run_info group under 'entry' group
            elif "run_info" == key:
                # Create run_info group
                run_info_group = entry.create_group(key)
                # Add attribute
                run_info_group.attrs["NX_class"] = "NXcollection"
                run_info_group.attrs["description"] = (
                    "Copy of the start and stop document from the bluesky run"
                )
                # Write data to the run_info_group
                write_collection(run_info_group, value)

            # Treat everything else as entry metadata
            else:
                if isinstance(value, (str, int, float)):
                    entry.create_dataset(key, data=value)
                elif isinstance(value, (list, np.ndarray)):
                    entry.create_dataset(key, data=np.array(value))

        logger.info("NeXus file '%s' created successfully.", file_path)


def write_collection(group, data: dict) -> None:
    """Write collection.

    Recursively writes a collection of data (nested dictionaries, lists, and
    primitive values) to a given group in a hierarchical storage structure.
    Scalars are stored as 1D arrays.

    Args:
        group (h5py.Group): The group where the data will be stored.
        data (dict): The data dictionary to be written.

    Raises:
        TypeError: If an unsupported data type is encountered.
    """
    string_dtype = h5py.string_dtype(encoding="utf-8")

    for key, value in data.items():
        if isinstance(value, dict):
            # Create a subgroup for nested data dictionaries
            subgroup = group.create_group(key)
            write_collection(subgroup, value)

        elif isinstance(value, (int, float, bool)):
            # Store scalar as 1D array
            group.create_dataset(key, data=np.array([value]))

        elif isinstance(value, str):
            # Store string as 1D array with UTF-8 dtype
            group.create_dataset(key, data=np.array([value], dtype=string_dtype))

        elif isinstance(value, (list, tuple)):
            # List or tuple with nested list or tuple elements
            if any(isinstance(item, (list, tuple)) for item in value):
                # Serialize nested structure into a single string
                serialized_value = str(value)
                group.create_dataset(
                    key, data=np.array([serialized_value], dtype=string_dtype)
                )
            # List or tuple without nested list or tuple elements
            else:
                if len(value) == 0:
                    # Empty list or tuple
                    group.create_dataset(key, data=np.array([], dtype=string_dtype))
                elif all(isinstance(item, (int, float, bool)) for item in value):
                    group.create_dataset(key, data=np.array(value))
                else:
                    # Convert mixed-type or string-containing list to strings
                    str_value = [str(item) for item in value]
                    group.create_dataset(
                        key, data=np.array(str_value, dtype=string_dtype)
                    )

        else:
            logger.error("Unsupported type '%s' for key '%s'", type(value), key)
            raise TypeError(f"ERROR: Unsupported type {type(value)} for key '{key}'")
