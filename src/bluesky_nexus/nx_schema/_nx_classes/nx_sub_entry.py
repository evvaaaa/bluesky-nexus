"""Contains the definition for NXsubentry."""

from .._nx_base import add_nx_class_basemodel
from .nx_object import NxObject


@add_nx_class_basemodel
class NxSubEntry(NxObject):
    """Represents an NeXus NXsubentry."""
