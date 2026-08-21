"""Contains the definition for NXsubentry."""

from bluesky_nexus.base_schema import (
    add_nx_class_basemodel,
)

from .nx_object import NxObject


@add_nx_class_basemodel
class NxSubEntry(NxObject):
    """Represents an NeXus NXsubentry."""
