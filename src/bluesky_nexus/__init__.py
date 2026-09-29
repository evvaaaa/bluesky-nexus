"""bluesky-nexus

A package for generating a standard NeXus structure for bluesky plans.
"""

from importlib.metadata import version

from .callbacks import BlueskyNexusCallback, NexusHdfWriterCallback
from .device import NxDevice
from .structure import DataKeyData, ObjectData, RunData, StreamData, create_nexus_structure

__version__ = version("bluesky_nexus")

__all__ = [
    "__version__",
    "BlueskyNexusCallback",
    "NexusHdfWriterCallback",
    "NxDevice",
    "RunData",
    "StreamData",
    "ObjectData",
    "DataKeyData",
    "create_nexus_structure",
]
