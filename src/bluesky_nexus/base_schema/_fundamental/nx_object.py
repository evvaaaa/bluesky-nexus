"""Contains the definition for NXobject."""

from .._building_blocks import (
    NxGroup,
    add_nx_class_basemodel,
)


@add_nx_class_basemodel
class NxObject(NxGroup):
    """Represents an NeXus NXobject."""
