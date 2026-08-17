"""Contains the definition for NXmonochromator."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_aperture import NxAperture
from .nx_component import NxComponent
from .nx_data import NxData


@add_nx_class_basemodel
class NxMonochromator(NxComponent):
    """Represents a NeXus NXmonochromator.

    Additional NxCrystal, NXvelocity_selector, NXgrating, NXoff_geometry
    of any name are to be expected in `NXmonochromator` classes.
    """

    wavelength: NxField | None = None
    """Selected wavelength."""

    wavelength_errors: NxField | None = None
    """Wavelength standard deviation."""

    energy: NxField | None = None
    """Energy selected."""

    energy_errors: NxField | None = None
    """Energy standard deviation."""

    energy_dispersion: NxField | None = None
    """Energy dispersion at exit slit."""

    wavelength_dispersion: NxField | None = None
    """Wavelength dispersion at exit slit."""

    depends_on: NxField | None = None
    """Add a definition for the reference point of a monochromator."""

    entrance_slit: NxAperture | None = None
    """Size, position and shape of the entrance slit of the monochromator."""

    exit_slit: NxAperture | None = None
    """Size, position and shape of the exit slit of the monochromator."""

    distribution: NxData | None = None
    """The distribution of the monochromator."""
