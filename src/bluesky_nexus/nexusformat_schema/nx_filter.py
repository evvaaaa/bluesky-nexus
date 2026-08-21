"""Contains the definition for NXfilter."""

from bluesky_nexus.base_schema import (
    NxField,
    add_nx_class_basemodel,
)

from .nx_component import NxComponent
from .nx_data import NxData
from .nx_log import NxLog


@add_nx_class_basemodel
class NxFilter(NxComponent):
    """Represents a NeXus NXfilter."""

    description: NxField | None = None
    """Composition of the filter. Chemical formula can be specified separately."""

    status: NxField | None = None
    """Is the filter enabled? "in" for yes "out" for no."""

    temperature: NxField | None = None
    """Average/nominal filter temperature."""

    thickness: NxField | None = None
    """Thickness of the filter."""

    density: NxField | None = None
    """Mass density of the filter."""

    chemical_formula: NxField | None = None
    """The chemical formula specified using CIF conventions. Abbreviated version
    of CIF standard."""

    unit_cell_a: NxField | None = None
    """Unit cell lattice parameter: length of side a."""

    unit_cell_b: NxField | None = None
    """Unit cell lattice parameter: length of side b."""

    unit_cell_c: NxField | None = None
    """Unit cell lattice parameter: length of side c."""

    unit_cell_alpha: NxField | None = None
    """Unit cell lattice parameter: angle alpha."""

    unit_cell_beta: NxField | None = None
    """Unit cell lattice parameter: angle beta."""

    unit_cell_gamma: NxField | None = None
    """Unit cell lattice parameter: angle gamma."""

    unit_cell_volume: NxField | None = None
    """Volume of the unit cell."""

    orientation_matrix: NxField | None = None
    """Orientation matrix of single crystal filter using Busing-Levy convention:
    W. R. Busing and H. A. Levy (1967). Acta Cryst. 22, 457-46."""

    m_value: NxField | None = None
    """m value of supermirror filter."""

    substrate_material: NxField | None = None
    """Substrate material of supermirror filter."""

    ssubstrate_thickness: NxField | None = None
    """Substrate thickness of supermirror filter."""

    coating_material: NxField | None = None
    """Coating material of supermirror filter."""

    substrate_roughness: NxField | None = None
    """Substrate roughness (RMS) of supermirror filter."""

    coating_roughness: NxField | None = None
    """Coating roughness (RMS) of supermirror filter."""

    depends_on: NxField | None = None
    """Add a definition for the reference point of a filter."""

    transmission: NxData | None = None
    """Wavelength transmission profile of filter."""

    temperature_log: NxLog | None = None
    """Linked temperature_log for the filter."""

    # TODO: Too many basemodel to define than I have time for
    # if I add this now.
    # sensor_type: NxSensor | None = None
    # """Sensor(s)used to monitor the filter temperature."""
