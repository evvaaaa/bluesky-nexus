"""
Contains the logic for specifying NeXus classes from the
bluesky device layer.
"""

from ._nx_device import NxDevice
from ._bluesky_nexus_hints import NxHints

__all__ = ["NxDevice", "NxHints"]
