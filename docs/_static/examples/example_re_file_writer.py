from bluesky import RunEngine
from pathlib import Path
from bluesky_nexus.callbacks import NexusHdfWriterCallback

RE = RunEngine()
# Will output a hdf5 file for each bluesky plan.
RE.subscribe(NexusHdfWriterCallback(Path("."))) 
