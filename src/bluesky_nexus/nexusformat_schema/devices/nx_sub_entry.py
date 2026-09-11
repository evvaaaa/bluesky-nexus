"""Contains the definition for NXsubentry."""

from bluesky_nexus.base_schema import NxObject, add_nx_class_basemodel


@add_nx_class_basemodel
class NxSubEntry(NxObject):
    """Represents an NeXus NXsubentry."""
