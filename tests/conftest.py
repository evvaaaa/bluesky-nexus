from pathlib import Path, PurePath

import pytest
from bluesky import RunEngine

from bluesky_nexus import NexusWriter


@pytest.fixture()
def tmpdir(tmpdir: PurePath):
    """Quick patch to get the full Path object from the PurePath."""
    return Path(tmpdir)


@pytest.fixture()
def RE_directly_subscribed(tmpdir: Path):
    RE = RunEngine()
    RE.subscribe(NexusWriter(tmpdir))
    return RE
