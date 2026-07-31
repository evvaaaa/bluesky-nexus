"""Some utils for tests."""

from pathlib import Path

from nexusformat import nexus


def load_only_generated_nexus_file(directory: Path) -> nexus.NXgroup:
    """Load the nexus file into a nexusformat.nexus.NXroot."""
    files_in_directory = list(Path(directory).iterdir())
    assert len(files_in_directory) == 1
    return nexus.nxload(files_in_directory[0])
