"""Pydantic schema for defining connections between `HasHints` devices and
nexusformat base classes for the nexusformat schema definitions:

https://github.com/nexpy/nexusformat/tree/main/src/nexusformat/definitions

For documentation on the standard for these classes, see:

https://manual.nexusformat.org/classes/base_classes/complete-structure.html

Throughout all classes, deprecated fields have been left absent.

These should eventually be stored seperate and in their own package seperate from
bluesky-nexus.

Many devices are simple reproductions of the NXDL, and others implement their own
validation logic that the device is correct, for example in ``NxData``,
``axes`` and ``signal`` are validated in the pydantic schema more dynamically.

Eventually it is hoped that there will be a novel generation method to generate
pydantic schema from NXDL.
"""

from .devices.nx_aperture import NxAperture
from .devices.nx_crystal import NxCrystal
from .devices.nx_detector import NxDetector
from .devices.nx_filter import NxFilter
from .devices.nx_grating import NxGrating
from .devices.nx_monochromator import NxMonochromator
from .devices.nx_note import NxNote
from .devices.nx_off_geometry import NxOff_Geometry
from .devices.nx_positioner import NxPositioner
from .devices.nx_sub_entry import NxSubEntry
from .devices.nx_transformations import NxTransformations
from .devices.nx_velocity_selector import NxVelocity_Selector

__all__ = [
    "NxAperture",
    "NxCrystal",
    "NxDetector",
    "NxFilter",
    "NxGrating",
    "NxMonochromator",
    "NxNote",
    "NxOff_Geometry",
    "NxPositioner",
    "NxSubEntry",
    "NxTransformations",
    "NxVelocity_Selector",
]
