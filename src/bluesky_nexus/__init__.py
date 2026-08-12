"""bluesky-nexus

A package for generating a standard NeXus structure for bluesky plans.
"""

from importlib.metadata import version

from .nx_callback import NexusCallback
from .nx_consumers import NexusHdfWriter
from .nx_device import NexusDevice

__version__ = version("bluesky_nexus")

__all__ = ["__version__", "NexusCallback", "NexusDevice", "NexusHdfWriter"]
