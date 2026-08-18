"""Pydantic schema for defining connections between `HasHints` devices and
nexusformat base classes:
https://manual.nexusformat.org/classes/base_classes/complete-structure.html

Throughout all classes, deprecated fields have been left abscent.

These should eventually be stored seperate and in their own package.
"""

from ._nx_attribute import NxAttribute
from ._nx_base import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NX_CLASS_TO_BASEMODEL,
    NxBase,
    NxField,
    NxGroup,
    add_nx_class_basemodel,
)
from ._nx_classes.nx_aperture import NxAperture
from ._nx_classes.nx_component import NxComponent
from ._nx_classes.nx_crystal import NxCrystal
from ._nx_classes.nx_data import NxData
from ._nx_classes.nx_detector import NxDetector
from ._nx_classes.nx_grating import NxGrating
from ._nx_classes.nx_log import NxLog
from ._nx_classes.nx_monochromator import NxMonochromator
from ._nx_classes.nx_note import NxNote
from ._nx_classes.nx_object import NxObject
from ._nx_classes.nx_off_geometry import NxOff_Geometry
from ._nx_classes.nx_positioner import NxPositioner
from ._nx_classes.nx_sub_entry import NxSubEntry
from ._nx_classes.nx_velocity_selector import NxVelocity_Selector

__all__ = [
    "NxAttribute",
    "NxAperture",
    "NxComponent",
    "NxCrystal",
    "NxGrating",
    "NxLog",
    "NxVelocity_Selector",
    "NxMonochromator",
    "NxNote",
    "NxOff_Geometry",
    "NxBase",
    "NX_CLASS_TO_BASEMODEL",
    "NxDetector",
    "NxField",
    "NxGroup",
    "NxObject",
    "NxPositioner",
    "NxSubEntry",
    "NxData",
    "add_nx_class_basemodel",
    "NX_ATTRIBUTE_SERIALIZED_PREFIX",
]
