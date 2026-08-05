"""Some utils for tests."""

import time
from pathlib import Path

from nexusformat import nexus


def load_only_generated_nexus_file(directory: Path) -> nexus.NXgroup:
    """Load the nexus file into a nexusformat.nexus.NXroot."""
    files_in_directory = [p for p in Path(directory).iterdir() if p.suffix == ".nxs"]
    assert len(files_in_directory) == 1
    return nexus.nxload(files_in_directory[0])


def wait_for_nexus_file(
    directory: Path, timeout: float = 5.0, poll_interval: float = 0.05
) -> nexus.NXgroup:
    """Wait until a file appears in `directory` and return its Path.
    Raises TimeoutError if no file appears within `timeout` seconds.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        files = [p for p in directory.iterdir() if p.is_file() and p.suffix == ".nxs"]
        if files:
            # If multiple files, return the most recently modified one.
            return load_only_generated_nexus_file(directory)
        time.sleep(poll_interval)
    raise TimeoutError(f"No file appeared in {directory!s} within {timeout} seconds")


def get_logs(directory: Path) -> Path:
    potential = directory / "nx_log.log"
    if not potential.exists():
        raise ValueError("Log directory not found")
    return potential
