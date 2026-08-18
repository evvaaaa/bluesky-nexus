"""Pydantic schema for defining connections between `HasHints` devices and
nexusformat base classes:
https://manual.nexusformat.org/classes/base_classes/complete-structure.html

Throughout all classes, deprecated fields have been left absent.

These should eventually be stored seperate and in their own package seperate from
bluesky nexus.
"""

from .nx_aperture import NxAperture
from .nx_component import NxComponent
from .nx_crystal import NxCrystal
from .nx_data import NxData
from .nx_detector import NxDetector
from .nx_grating import NxGrating
from .nx_log import NxLog
from .nx_monochromator import NxMonochromator
from .nx_note import NxNote
from .nx_object import NxObject
from .nx_off_geometry import NxOff_Geometry
from .nx_positioner import NxPositioner
from .nx_sub_entry import NxSubEntry
from .nx_velocity_selector import NxVelocity_Selector

__all__ = [
    "NxAperture",
    "NxComponent",
    "NxCrystal",
    "NxData",
    "NxDetector",
    "NxGrating",
    "NxLog",
    "NxMonochromator",
    "NxNote",
    "NxObject",
    "NxOff_Geometry",
    "NxPositioner",
    "NxSubEntry",
    "NxVelocity_Selector",
]
