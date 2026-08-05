"""Pydantic schema for validating the dictionary/yaml."""

from ._nx_classes.nx_detector import NxDetector
from ._nx_classes.nx_object import NxObject
from .nx_base import NX_CLASS_TO_BASEMODEL, NxField, NxGroup, add_nx_class_basemodel

__all__ = [
    "add_nx_class_basemodel",
    "NxGroup",
    "NxField",
    "NxObject",
    "NxDetector",
    "NX_CLASS_TO_BASEMODEL",
]
