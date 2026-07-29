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

from pathlib import Path

from event_model import RunStop, documents
from event_model.documents import Document, RunStart

from bluesky_nexus import __version__
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.nx_writer._file_writer import NexusFileWriter

from ._data_extractor import RunData
from .constants import (
    NX_FILE_EXTENSION,
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


class NexusWriter:
    """Callback that builds NeXus files from Bluesky run documents.

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

        self._run_data: RunData | None = None

    def __call__(self, name: str, document: Document):
        """Extract the nexus and detector information throughtout the run
        and then produce a file on run_stop.
        """
        if name == "start":
            self.run_start(document)  # type: ignore
            return
        if self._run_data is None:
            logger.warning(f"Received {name} without a run start...")
            return

        if name == "descriptor":
            self._run_data.extract_descriptor(document)  # type: ignore
        elif name == "event":
            self._run_data.extract_event(document)  # type: ignore
        elif name == "event_page":
            self._run_data.extract_event_page(documents)  # type: ignore
        elif name == "stop":
            self.run_stop(document)  # type: ignore

    def run_start(self, document: RunStart):
        """Create a parser for capturing run information."""
        self._run_data = RunData(document)

    def run_stop(self, document: RunStop):
        """
        Triggers the process of generating the NeXus file by calling
        `generate_nexus_file()`.

        This method acts as a simple entry point for processing the
        metadata and writing the NeXus file.
        """
        if self._run_data is None:
            return
        self._run_data.run_stop = document  # type: ignore

        path = _create_nx_file_path(
            self.nx_file_root_dir_path, self._run_data.run_start
        )
        writer = NexusFileWriter(path)
        writer.create_file(self._run_data)
