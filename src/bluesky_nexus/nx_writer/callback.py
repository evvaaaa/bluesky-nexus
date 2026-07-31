"""NeXus Writer callback for bluesky plans."""

from datetime import datetime
from pathlib import Path

from event_model import RunStop, documents
from event_model.documents import Document, RunStart

from bluesky_nexus import __version__
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.constants import (
    DEFAULT_PLAN_NAME,
    NX_FILE_EXTENSION,
)
from bluesky_nexus.nx_writer._file_writer import NexusFileWriter

from ._data_extractor import RunData


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

    The file name is generated automatically from the run start plan name and
    plan start time.
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

    file_name = (
        f"{datetime.fromtimestamp(start['time']).strftime('%Y-%m-%d-%H-%M-%S')}-"
        f"{start.get('plan_name', DEFAULT_PLAN_NAME)}"
    )
    file_name = f"{file_name.lstrip(NX_FILE_EXTENSION)}{NX_FILE_EXTENSION}"

    return dir_path / file_name


class NexusWriter:
    """Callback that builds NeXus files from Bluesky run documents.

    Parameters
    ----------
    nx_file_root_dir_path : Path
        Root directory where NeXus files are stored. Files will subs
    """

    def __init__(self, root_output_directory: Path) -> None:
        """Init.

        Initialize with NeXus file path and component name delimiter.
        """
        if not root_output_directory.is_dir():
            raise ValueError(
                f"Selected output path {root_output_directory} is not a directory."
            )

        self._root_output_directory = root_output_directory

        # Log the version of the package
        logger.info(f"NexusWriter Initialized: version - {__version__}")
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
        self._run_data = RunData(document, document["time"])

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
            self._root_output_directory, self._run_data.run_start
        )
        writer = NexusFileWriter(path)
        writer.create_file(self._run_data)
