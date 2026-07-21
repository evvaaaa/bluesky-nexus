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
from pathlib import Path
from typing import cast

from bluesky.callbacks.core import CollectThenCompute
from event_model import PerObjectHint
from event_model.documents import Event, EventDescriptor, RunStart

from bluesky_nexus import __version__
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.nx_writer._document_parser import ParsedDevice
from bluesky_nexus.nx_writer._file_writer import NexusFileWriter

from .constants import (
    NX_FILE_EXTENSION,
    NX_MD_KEY,
)


def _create_nx_file_path(root_directory: Path, start: RunStart) -> Path:
    """Construct the full NeXus file path.

    This method builds the hierarchical directory structure and the final
    NeXus filename using metadata from the start document. It ensures that all
    directories exist and that the filename adheres to the naming scheme used
    by the NexusWriter.

    Directory layout:
        {self.nx_file_root_dir_path}/{project_name}/{sub_project_name}/
        {self.nx_file_root_dir_path}/{project_name}/
        {self.nx_file_root_dir_path}/

    Filename format:
        {scan_id:04d}_{plan_name}_{uid8}.nx

        - scan_id is zero-padded to 4 digits (e.g., 15 → "0015")
        - uid8 is the first 8 characters of the UID with all dashes removed
        - plan_name is taken from the start document
        - If `nx_file_name` is provided in the metadata, it overrides the
        auto-generated name (extension is appended if missing)

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
    # Extract 'project_name' and 'sub_project_name' from metadata passed to the run
    project_name = start.get("project_name")
    sub_project_name = start.get("sub_project_name")

    dir_path: Path = root_directory
    if isinstance(project_name, str) and project_name.strip():
        dir_path = dir_path / project_name.strip()

        if isinstance(sub_project_name, str) and sub_project_name.strip():
            dir_path = dir_path / sub_project_name.strip()
        elif sub_project_name is not None:
            logger.info(
                "Run %s contained sub_project_name=%r, but it was not a "
                "non-empty string. Writing under project directory %s only.",
                start.get("uid"),
                sub_project_name,
                dir_path,
            )
    elif project_name is not None:
        logger.info(
            "Run %s contained project_name=%r, but it was not a non-empty string. "
            "Writing under root output directory %s.",
            start.get("uid"),
            project_name,
            dir_path,
        )
    else:
        logger.debug(
            "Run %s did not contain project_name. "
            "Writing under root output directory %s.",
            start.get("uid"),
            dir_path,
        )

    # Create the directories if they do not exist
    dir_path.mkdir(parents=True, exist_ok=True)

    nx_file_name: str = start.get("nx_file_name", None)

    if nx_file_name and nx_file_name.strip():
        file_name = nx_file_name.strip()
    else:  # Auto-generate filename
        scan_id: int = start["scan_id"]  # type: ignore
        plan_name: str = start["plan_name"]  # type: ignore
        uid: str = start["uid"]

        scan_id_str = f"{scan_id:04d}"

        # Take only the first 8 characters of the UID (remove "-")
        uid_short = uid.replace("-", "")[:8]
        file_name = f"{scan_id_str}_{plan_name}_{uid_short}"

    if not file_name.endswith(NX_FILE_EXTENSION):
        file_name += NX_FILE_EXTENSION

    return dir_path / file_name


def _get_schemas(descriptors: deque[EventDescriptor]) -> dict[str, dict]:
    schemas = {}
    for descriptor in descriptors:
        for object_key, hint in descriptor.get("hints", {}).items():
            hint = cast(PerObjectHint, hint)
            if "NX_schema" in hint:
                schemas.update({object_key: hint["NX_schema"]})
    return schemas


def _get_datakeys(descriptors: deque[EventDescriptor]) -> set:
    """Find out devices/objects of a run.

    Collects all unique keys from 'configuration' and
    'object_keys' in a deque of Bluesky descriptors.

    Args:
        descriptors (deque): deque containing descriptor dictionaries

    Returns:
        set: a set of unique keys found under 'configuration' and 'object_keys'
    """
    keys = set()

    for descriptor in descriptors:
        # Collect keys under 'configuration'
        configuration = descriptor.get("configuration", {})
        keys.update(configuration.keys())

        # Collect keys under 'object_keys'
        datakeys = descriptor.get("data_keys", {})
        keys.update(datakeys.keys())

    logger.debug("Collected unique descriptor keys: %s", keys)
    return keys


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
        - Create hierarchical directories based on `project_name` and
          `sub_project_name`.
        - Construct standardized filenames:
              {scan_id:04d}_{plan_name}_{uid8}.nx
        - Write NeXus groups: NXentry, NXinstrument, NXcollection.

    Parameters
    ----------
    nx_file_root_dir_path : Path
        Root directory where NeXus files are stored in a structured way
    """

    def __init__(self, nx_file_root_dir_path: Path) -> None:
        """Init.

        Initialize with NeXus file path and component name delimiter.
        """
        super().__init__()  # Initialize the parent class
        self.nx_file_root_dir_path = nx_file_root_dir_path

        # Check if 'nx_file_root_dir_path' is pointing to existing directory
        if not nx_file_root_dir_path.is_dir():
            raise ValueError(
                f"Nexus root dir path: {nx_file_root_dir_path} is not a directory."
            )

        # Log the version of the package
        logger.info(f"bluesy_nexus_writer: version: {__version__}")

    def descriptor(self, doc: EventDescriptor):
        """Handle descriptor documents for streams relevant to NeXus.

        Only descriptors from the "primary" or "baseline" streams are
        collected. Other streams are ignored for NeXus file generation.
        """
        if doc["name"] in ("primary", "baseline"):  # type: ignore
            super().descriptor(doc)

    def event(self, doc: Event) -> Event:  # type: ignore
        """Handle event documents belonging to accepted descriptors.

        Events are processed only if their descriptor UID matches one of
        the stored descriptors handled by `descriptor()`.
        """
        if doc["descriptor"] in (d["uid"] for d in self._descriptors):
            super().event(doc)
        return doc

    def compute(self) -> None:
        """
        Triggers the process of generating the NeXus file by calling
        `generate_nexus_file()`.

        This method acts as a simple entry point for processing the
        metadata and writing the NeXus file.
        """
        if self._start_doc is None or self._stop_doc is None:
            return

        path = _create_nx_file_path(self.nx_file_root_dir_path, self._start_doc)
        writer = NexusFileWriter(path)
        writer.create_file(
            {
                "start": copy.deepcopy(self._start_doc),
                "stop": copy.deepcopy(self._stop_doc),
            }
        )

        _descriptor_uid_to_parsed_device = {}
        for descriptor in self._descriptors:
            parsed_devices = [
                ParsedDevice(object_key)
                for object_key in descriptor.get("object_keys", {})
            ]
            for device in parsed_devices:
                device.descriptor(descriptor)
            _descriptor_uid_to_parsed_device[descriptor["uid"]] = parsed_devices

        for event in self._events:
            parsed_devices = _descriptor_uid_to_parsed_device[event["descriptor"]]
            for device in parsed_devices:
                device.event(event)

        # TODO: event pages

        for descriptor in self._descriptors:
            writer.write_stream(
                descriptor["name"], _descriptor_uid_to_parsed_device[descriptor["uid"]]
            )

        self.reset()  # Clears the cached documents
