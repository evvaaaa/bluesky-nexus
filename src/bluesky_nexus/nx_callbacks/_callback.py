"""NeXus Writer callback for bluesky plans."""

from abc import ABC, abstractmethod
from importlib.metadata import version
from typing import Any

from event_model import RunStop, documents
from event_model.documents import Document, RunStart
from nexusformat import nexus

from bluesky_nexus.logger import LOGGER
from bluesky_nexus.nx_structure import RunData, create_nexus_structure

__version__ = version("bluesky_nexus")


class BlueskyNexusCallback(ABC):
    """Callback that builds a new NeXus NXroot per plan and passes it to
    process_nexus_structure."""

    def __init__(self) -> None:
        """Initialize the NeXus callback and save consumers."""
        # Log the version of the package
        LOGGER.info(f"NexusCallback Initialized: version - {__version__}")
        self._run_data: RunData | None = None

    def __call__(self, name: str, document: Document) -> None:
        """Extract the nexus and detector information throughtout the run
        and then produce a file on run_stop.
        """
        if name == "start":
            self.run_start(document)  # type: ignore
            return
        if self._run_data is None:
            LOGGER.warning(f"Received {name} without a run start...")
            return

        if name == "descriptor":
            self._run_data.extract_descriptor(document)  # type: ignore
        elif name == "event":
            self._run_data.extract_event(document)  # type: ignore
        elif name == "event_page":
            self._run_data.extract_event_page(documents)  # type: ignore
        elif name == "stop":
            self.run_stop(document)  # type: ignore

    def run_start(self, document: RunStart) -> None:
        """Create a parser for capturing run information."""
        self._run_data = RunData(document, document["time"])

    def run_stop(self, document: RunStop) -> None:
        """Create and return the nexus structure for the plan."""
        if self._run_data is None:
            return
        self._run_data.run_stop = document  # type: ignore

        nexus_structure = create_nexus_structure(self._run_data)
        self.process_nexus_structure(nexus_structure)

    @abstractmethod
    def process_nexus_structure(self, generated_structure: nexus.NXroot) -> Any:
        """Abstract method where the nexus structure generated through this callback
        can be processed in subclasses. For an example see `NexusHdfWriterCallback`."""
