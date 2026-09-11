"""Contains the definition for NXaperture."""

from bluesky_nexus.base_schema import NxComponent, NxField, add_nx_class_basemodel


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
    """Shape of the aperture."""

    size: NxField | None = None
    """The relevant dimension for the aperture, i.e. slit width, pinhole and iris diameter."""
