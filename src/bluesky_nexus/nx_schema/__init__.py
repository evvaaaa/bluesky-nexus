"""Pydantic schema for defining connections between `HasHints` devices and nexus classes."""

from ._nx_attribute import NxAttribute
from ._nx_base import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NX_CLASS_TO_BASEMODEL,
    NxBase,
    NxField,
    NxGroup,
    add_nx_class_basemodel,
)
from ._nx_classes.nx_data import NxData
from ._nx_classes.nx_detector import NxDetector
from ._nx_classes.nx_object import NxObject
from ._nx_classes.nx_positioner import NxPositioner
from ._nx_classes.nx_sub_entry import NxSubEntry

__all__ = [
    "NxAttribute",
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
