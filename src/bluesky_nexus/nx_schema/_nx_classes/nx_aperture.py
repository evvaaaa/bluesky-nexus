"""Contains the definition for NXaperture."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_component import NxComponent


@add_nx_class_basemodel
class NxAperture(NxComponent):
    """Represents a NeXus NXaperture.

    Additional NXoff_geometry, NXpositioner, NXnote
    name are to be expected in `NXaperture` classes.
    """

    depends_on: NxField | None = None
    """The reference point of the aperture is its center in the x and y axis. The reference
    point on the z axis is the surface of the aperture pointing towards the source."""

    material: NxField | None = None
    """Absorbing material of the aperture."""

    description: NxField | None = None
    """Description of aperture."""

    shape: NxField | None = None
    """Shape of the aperture.

    TODO: I'm now considering if we allow constant NxField values as well.
    There's no situation where this would be specified as a datakey exactly,
    but it's also not an attribute.
    """

    size: NxField | None = None
    """The relevant dimension for the aperture, i.e. slit width, pinhole and iris diameter."""
