"""Contains the definition for NXobject."""

from bluesky_nexus.nx_schema import (
    NxGroup,
    add_nx_class_basemodel,
)


@add_nx_class_basemodel
class NxObject(NxGroup):
    """Represents an NeXus NXobject."""
