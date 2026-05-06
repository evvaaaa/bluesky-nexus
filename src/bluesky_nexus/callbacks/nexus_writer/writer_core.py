"""NeXus Writer Module for Bluesky Runs.

This module provides the core functionality to create NeXus files in HDF5
format based on Bluesky run documents (start, event, descriptor, stop).
It implements the logic used by the `NexusWriter` callback, including:

    • extracting run information
    • processing NeXus metadata templates (nexus_md)
    • resolving $post-run placeholders using descriptors and events
    • filtering out unused devices based on descriptors
    • constructing standardized NeXus file paths and filenames
    • writing the NeXus hierarchy (NXentry, NXinstrument, NXcollection)
    • automatic directory creation for project_name/sub_project_name

The module follows the NeXus standard and produces files suitable for
data archival and beamline data workflows.
"""

import copy
from collections import deque
from functools import partial
from pathlib import Path
from typing import Any, Deque, Dict, Tuple, cast

import h5py  # type: ignore
import numpy as np
from bluesky.callbacks.core import CollectThenCompute
from event_model.documents import Document, Event, EventDescriptor, RunStart, RunStop

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
from bluesky_nexus.common.version_utils import log_package_version


class NexusWriter(CollectThenCompute):
    """Callback that builds NeXus files from Bluesky run documents.

    The NexusWriter collects metadata and data from the RunEngine
    (start, descriptor, event, and stop documents), processes NeXus metadata
    templates (`nexus_md`), resolves $post-run placeholders, filters out devices
    not used in the run, constructs the output directory and filename, and
    finally generates a valid NeXus file in HDF5 format.

    Key responsibilities:
        - Collect run documents through the Bluesky callback interface.
        - Filter device metadata to include only devices present in descriptors.
        - Resolve post-run metadata placeholders using descriptors and events.
        - Create hierarchical directories based on `project_name` and `sub_project_name`.
        - Construct standardized filenames:
              {scan_id:04d}_{plan_name}_{uid8}.nx
        - Write NeXus groups: NXentry, NXinstrument, NXcollection.

    Parameters
    ----------
    nx_file_root_dir_path : Path
        Root directory where NeXus files are stored in a structured way
    cpt_name_delimiter : str, optional
        Delimiter separating component names in device keys.
        Default is "_" (standard for Ophyd).
    """

    def __init__(
        self, nx_file_root_dir_path: Path, cpt_name_delimiter: str = "_"
    ) -> None:
        """Init.

        Initialize with NeXus file path and component name delimiter.
        """
        super().__init__()  # Initialize the parent class
        self.nx_file_root_dir_path = nx_file_root_dir_path
        self.cpt_name_delimiter = cpt_name_delimiter

        # Log the version of the package
        log_package_version()

    def descriptor(self, doc: EventDescriptor):
        """Handle descriptor documents for streams relevant to NeXus.

        Only descriptors from the "primary" or "baseline" streams are
        collected. Other streams are ignored for NeXus file generation.
        """
        if doc["name"] in ("primary", "baseline"):  # type: ignore
            super().descriptor(doc)

    def event(self, doc: Event) -> Event:
        """Handle event documents belonging to accepted descriptors.

        Events are processed only if their descriptor UID matches one of
        the stored descriptors handled by `descriptor()`.
        """
        if doc["descriptor"] in (d["uid"] for d in self._descriptors):
            super().event(doc)
        return doc

    def __call__(
        self, name: str, doc: Dict[str, Any], validate: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """Dispatch a Bluesky document to its corresponding handler.

        This method overrides ``DocumentRouter.__call__`` to route incoming
        Bluesky documents (``start``, ``descriptor``, ``event``, ``stop``) to
        the appropriate callback method of the ``NexusWriter``. The document is
        first cast to its concrete type (``RunStart``, ``EventDescriptor``,
        ``Event``, or ``RunStop``) to ensure proper type checking inside each
        handler.

        Parameters
        ----------
        name : str
            The type of document emitted by the RunEngine. Expected values are
            ``"start"``, ``"descriptor"``, ``"event"``, or ``"stop"``.
        doc : dict
            The document payload associated with the given ``name``. The document
            is dynamically cast to the corresponding concrete type before being
            forwarded to the handler.
        validate : bool, optional
            Included to match the signature of ``DocumentRouter.__call__``.
            Validation is not performed by this implementation. Default is ``False``.

        Returns
        -------
        tuple[str, dict]
            A ``(name, doc)`` tuple, as required by ``DocumentRouter``'s calling
            convention. The returned document is the original input and is not
            modified by this method.

        Notes
        -----
        This method ensures that:
            - ``start`` documents are routed to ``start()``
            - ``descriptor`` documents are routed to ``descriptor()``
            - ``event`` documents are routed to ``event()``
            - ``stop`` documents are routed to ``stop()``

        Any other document type will silently bypass all handlers.
        """
        typed_doc = cast(Document, doc)

        if name == "start":
            self.start(cast(RunStart, typed_doc))

        elif name == "descriptor":
            self.descriptor(cast(EventDescriptor, typed_doc))

        elif name == "event":
            self.event(cast(Event, typed_doc))

        elif name == "stop":
            self.stop(cast(RunStop, typed_doc))

        return name, doc


    def create_nx_file_path(self, root_dir_path: Path) -> Path:
        """Construct the full NeXus file path.

        This method builds the hierarchical directory structure and the final
        NeXus filename using metadata from the start document. It ensures that all
        directories exist and that the filename adheres to the naming scheme used
        by the NexusWriter.

        Directory layout:
            {root_dir_path}/{project_name}/{sub_project_name}/
            {root_dir_path}/{project_name}/
            {root_dir_path}/

        Filename format:
            {scan_id:04d}_{plan_name}_{uid8}.nx

            - scan_id is zero-padded to 4 digits (e.g., 15 → "0015")
            - uid8 is the first 8 characters of the UID with all dashes removed
            - plan_name is taken from the start document
            - If `nx_file_name` is provided in the metadata, it overrides the
            auto-generated name (extension is appended if missing)

        Parameters
        ----------
        root_dir_path : Path
            Root directory where the NeXus file hierarchy should be created.

        Returns
        -------
        Path
            Full path to the NeXus file, guaranteed to be located inside the
            auto-created directory tree.

        Raises
        ------
        ValueError
            If the root directory path does not exist.

        Notes
        -----
        - When present and valid directories `{project_name}` and `{sub_project_name}`
            are created automatically.
        - The `.nx` extension is appended if missing.
        - This function does not open or write the file; it only returns a valid path.
        """

        # Check if 'root_dir_path' is pointing to existing directory
        if not root_dir_path.is_dir():
            raise ValueError(f"Nexus dir path {root_dir_path} is not a directory.")

        # Extract 'project_name' and 'sub_project_name' from metadata passed to the run
        project_name = self._start_doc.get("project_name")
        sub_project_name = self._start_doc.get("sub_project_name")

        dir_path: Path = root_dir_path
        if isinstance(project_name, str) and project_name.strip():
            dir_path = dir_path / project_name.strip()

            if isinstance(sub_project_name, str) and sub_project_name.strip():
                dir_path = dir_path / sub_project_name.strip()
            elif sub_project_name is not None:
                logger.info(
                    "Run %s contained sub_project_name=%r, but it was not a non-empty string. "
                    "Writing under project directory %s only.",
                    self._start_doc.get("uid"),
                    sub_project_name,
                    dir_path,
                )
        elif project_name is not None:
            logger.info(
                "Run %s contained project_name=%r, but it was not a non-empty string. "
                "Writing under root output directory %s.",
                self._start_doc.get("uid"),
                project_name,
                dir_path,
            )
        else:
            logger.debug(
                "Run %s did not contain project_name. Writing under root output directory %s.",
                self._start_doc.get("uid"),
                dir_path,
            )

        # Create the directories if they do not exist
        dir_path.mkdir(parents=True, exist_ok=True)

        # Retrieve nexus file name from metadata passed to the run
        nx_file_name: str = self._start_doc.get("nx_file_name", None)

        if nx_file_name and nx_file_name.strip():
            file_name = nx_file_name.strip()
        else:
            # Auto-generate filename
            scan_id: int = self._start_doc["scan_id"]
            plan_name: str = self._start_doc["plan_name"]
            uid: str = self._start_doc["uid"]

            # Format scan_id to 4 digits
            scan_id_str = f"{scan_id:04d}"

            # Take only the first 8 characters of the UID (remove "-")
            uid_short = uid.replace("-", "")[:8]

            # Construct the file name
            file_name = f"{scan_id_str}_{plan_name}_{uid_short}"

        # Add extension to file name
        if not file_name.endswith(NX_FILE_EXTENSION):
            file_name += NX_FILE_EXTENSION

        return dir_path / file_name

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
        """Construct and write the NeXus file.

        The method performs:
            1. Validation of required metadata (`nexus_md`) in the start document.
            2. Creation of the file path using `create_nx_file_path()`.
            3. Deep copying of the start document (docs are immutable).
            4. Filtering out unused devices based on descriptors.
            5. Resolving $post-run placeholders in NeXus metadata.
            6. Extracting a structured `run_info` dictionary.
            7. Combining instrument metadata with run_info.
            8. Writing the NeXus HDF5 file.
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

            logger.debug("Collected unique descriptor keys: %s", keys_set)
            return keys_set

        def filter_start_doc(
            start_doc_cpy: dict, keys_set: set, delimiter: str = "_"
        ) -> dict:
            """Remove md for devices not participating in run.

            Devices are kept only if:
                - The key exactly matches a descriptor key, OR
                - The key is a prefix of a descriptor key, followed by the delimiter.

            This filtering applies to:
                - start_doc_cpy["device_md"]
                - start_doc_cpy["nexus_md"]

            Returns
            -------
            dict
                Filtered copy of the start document.
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

                    # Log what will be removed (or if nothing to remove)
                    if keys_to_remove:
                        logger.debug(
                            "Keys to remove from '%s': %s",
                            section,
                            ", ".join(keys_to_remove),
                        )
                    else:
                        logger.debug("No keys to remove from '%s'", section)

                    for k in keys_to_remove:
                        del start_doc_cpy[section][k]
                        logger.debug(
                            (
                                "Device '%s' removed from '%s' of the start document "
                                "(not participating in plan)"
                            ),
                            k,
                            section,
                        )
            return start_doc_cpy

        # Check if NEXUS_MD_KEY is contained in the start document
        if NX_MD_KEY not in self._start_doc:
            logger.error(
                "The start document does not contain '%s' dictionary.", NX_MD_KEY
            )
            return

        # Create nexus file path
        nx_file_path: Path = self.create_nx_file_path(self.nx_file_root_dir_path)

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
        data: dict = {}

        if run_info:
            data.update({"run_info": run_info})
        else:
            logger.warning(
                "'run_info' is an empty dict. The 'NXcollection' group will not be "
                "included in the resulting NeXus file: %s.",
                nx_file_path,
            )

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
        else:
            logger.warning(
                "After filtering the start document, 'start_doc_cpy[%s]' is "
                "an empty dict. The 'NXinstrument' group will not be included "
                "in the resulting NeXus file: %s.",
                NX_MD_KEY,
                nx_file_path,
            )

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
            from the start document, excluding the 'nexus_md' key.
            The 'stop' key will include the entire stop
            document.

    Notes:
        - The 'nexus_md' key is intentionally excluded
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


def create_nexus_file(file_path: Path, data_dict: Dict[str, Any]) -> None:
    """Create nexus file.

    Creates a NeXus file at the specified file path using the provided data
    dictionary.

    Parameters:
        file_path (Path): The path where the NeXus file will be created.
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
