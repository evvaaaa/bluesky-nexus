"""Contains the definition for NXsubentry."""

from .._nx_base import NxGroup, add_nx_class_basemodel


@add_nx_class_basemodel
class NxSubEntry(NxGroup):
    """Represents an NeXus NXsubentry."""
