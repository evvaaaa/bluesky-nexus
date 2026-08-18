"""Contains the definition for NXvelocity_selector."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_component import NxComponent


@add_nx_class_basemodel
class NxVelocity_Selector(NxComponent):
    """Represents a NeXus NXvelocity_selector."""

    type: NxField | None = None
    """Velocity selector type."""

    rotation_speed: NxField | None = None
    """Velocity selector rotation speed."""

    radius: NxField | None = None
    """Radius at beam centre."""

    spwidth: NxField | None = None
    """Spoke width at beam centre."""

    length: NxField | None = None
    """Rotor length."""

    num: NxField | None = None
    """Number of spokes/lamella."""

    twist: NxField | None = None
    """Twist angle along axis."""

    table: NxField | None = None
    """Offset vertical angle."""

    height: NxField | None = None
    """Input beam height."""

    width: NxField | None = None
    """Input beam width."""

    wavelength: NxField | None = None
    """Wavelength."""

    wavelength_spread: NxField | None = None
    """Deviation FWHM /Wavelength."""

    depends_on: NxField | None = None
    """Add a definition for the reference point of a velocity selector."""
