from pathlib import Path

from bluesky import RunEngine

from bluesky_nexus.callbacks import HdfWriterCallback

RE = RunEngine()
# Will output a hdf5 file for each bluesky plan.
RE.subscribe(HdfWriterCallback(Path(".")))
