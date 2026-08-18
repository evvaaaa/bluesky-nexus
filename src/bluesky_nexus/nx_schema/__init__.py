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
from .nx_classes.nx_aperture import NxAperture
from .nx_classes.nx_component import NxComponent
from .nx_classes.nx_crystal import NxCrystal
from .nx_classes.nx_data import NxData
from .nx_classes.nx_detector import NxDetector
from .nx_classes.nx_grating import NxGrating
from .nx_classes.nx_log import NxLog
from .nx_classes.nx_monochromator import NxMonochromator
from .nx_classes.nx_note import NxNote
from .nx_classes.nx_object import NxObject
from .nx_classes.nx_off_geometry import NxOff_Geometry
from .nx_classes.nx_positioner import NxPositioner
from .nx_classes.nx_sub_entry import NxSubEntry
from .nx_classes.nx_velocity_selector import NxVelocity_Selector

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
