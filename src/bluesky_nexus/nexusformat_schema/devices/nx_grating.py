"""Contains the definition for NXgrating."""

from bluesky_nexus.base_schema import NxComponent, NxData, NxField, add_nx_class_basemodel


@add_nx_class_basemodel
class NxGrating(NxComponent):
    """Represents a NeXus NXgrating.

    Additional `NXoff_geometry`, `NXtransformations` are to be expected
    in `NXgrating` classes.
    """

    angles: NxField | None = None
    """Blaze or trapezoidal angles, with the angle of the upstream facing edge listed first.
    Blazed gratings can be identified by the low value of the first-listed angle."""

    period: NxField | None = None
    """List of polynomial coefficients describing the spatial separation of lines/grooves
    as a function of position along the grating, in increasing powers of position."""

    duty_cycle: NxField | None = None

    depth: NxField | None = None

    diffraction_order: NxField | None = None

    deflection_angle: NxField | None = None
    """Angle between the incident beam and the utilised outgoing beam."""

    interior_atmosphere: NxField | None = None
    """Any of these values: vacuum | helium | argon

    There's also not really a decent case to be made for why this wouldn't
    be an attribute in the nxdl.
    """

    substrate_material: NxField | None = None

    substrate_density: NxField | None = None

    substrate_thickness: NxField | None = None

    coating_material: NxField | None = None

    substrate_roughness: NxField | None = None

    coating_roughness: NxField | None = None

    layer_thickness: NxField | None = None
    """An array describing the thickness of each layer."""

    depends_on: NxField | None = None
    """Add a definition for the reference point of a bending grating."""

    figure_data: NxData | None = None
    """Numerical description of the surface figure of the mirror."""
