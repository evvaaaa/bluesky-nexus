"""Contains the definition for `NXobject`."""

from ..nx_base import NxGroup, add_nx_class_basemodel


@add_nx_class_basemodel
class NxObject(NxGroup):
    """Represents a NeXus object this is a parent class with no definitions."""
