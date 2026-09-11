"""Contains the definition for NXdetector_module."""

from typing import Literal

from bluesky_nexus.base_schema import (
    NxAttribute,
    NxConstantAttribute,
    NxField,
    NxObject,
    add_nx_class_basemodel,
)


class NxOffsetField(NxField):
    transformation_type: NxConstantAttribute[Literal["translation"]] = NxConstantAttribute(
        constant="translation"
    )

    vector: NxAttribute | None = None
    """Three values that define the axis for this transformation,"""

    offset: NxAttribute | None = None
    """A fixed offset applied before the transformation (three vector components)."""

    offset_units: NxAttribute | None = None
    """Units of the offset."""

    depends_on: NxAttribute | None = None
    """Points to the path of the next element in the geometry chain."""


@add_nx_class_basemodel
class NxDetector_Module(NxObject):
    """Represents a NeXus NXdetector_module."""

    data_origin: NxField | None = None
    """A dimension-2 or dimension-3 field which gives the indices of the origin of the hyperslab
    of data for this module in the main area detector image in the parent NXdetector module."""

    data_size: NxField | None = None
    """Two or three values for the size of the module in pixels in each direction.
    Dimensionality and order of indices is the same as for data_origin."""

    module_offset: NxOffsetField | None = None
    """Offset of the module in regards to the origin of the detector in an arbitrary direction."""

    fast_pixel_direction: NxOffsetField | None = None
    """Values along the direction of fastest varying pixel direction."""

    slow_pixel_direction: NxOffsetField | None = None
    """Values along the direction of slowest varying pixel direction."""

    depends_on: NxField | None = None
    """Points to the start of the dependency chain for this module."""
