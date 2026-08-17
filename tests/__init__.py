"""Some utils for tests."""

import time
from pathlib import Path

from nexusformat import nexus


def load_only_generated_nexus_file(
    directory: Path,
) -> nexus.NXgroup:
    """Load the nexus file into a nexusformat.nexus.NXroot."""
    files_in_directory = [p for p in Path(directory).iterdir() if p.suffix == ".nxs"]
    assert len(files_in_directory) == 1
    return nexus.nxload(files_in_directory[0])


def wait_for_nexus_file(
    directory: Path,
    timeout: float = 5.0,
    poll_interval: float = 0.05,
    wait_after_file_exists: float = 0.2,
) -> nexus.NXgroup:
    """Wait until a file appears in `directory` and return its Path.
    Raises TimeoutError if no file appears within `timeout` seconds.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        files = [p for p in directory.iterdir() if p.is_file() and p.suffix == ".nxs"]
        if files:
            # Once the file exists, we give the writer a little time to make
            # sure it's done.
            time.sleep(wait_after_file_exists)
            return load_only_generated_nexus_file(directory)
        time.sleep(poll_interval)
    raise TimeoutError(f"No file appeared in {directory!s} within {timeout} seconds")


def get_logs(directory: Path) -> Path:
    potential = directory / "test-log.log"
    if not potential.exists():
        raise ValueError("Log directory not found")
    return potential


def add_device_metadata_to_hints_wrapper(cls):
    """Minimal version of what bessyii device map does."""
    original_hints_getter = cls.hints.fget

    @property
    def new_hints(self):
        original = original_hints_getter(self)
        original.update({"metadata": getattr(self, "md", {})})
        return original

    cls.hints = new_hints
    return cls
