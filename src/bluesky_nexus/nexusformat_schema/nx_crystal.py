"""Contains the definition for NXcrystal."""

from bluesky_nexus.base_schema import NxField, add_nx_class_basemodel

from .nx_component import NxComponent
from .nx_data import NxData
from .nx_log import NxLog


@add_nx_class_basemodel
class NxCrystal(NxComponent):
    """Represents a NeXus NXcrystal.

    An additional key of `NxOff_Geometry` is o be expected.
    """

    usage: NxField | None = None
    """How this crystal is used. Choices are in the list.
    Either "Bragg" or "Laue".
    """

    type: NxField | None = None
    """Type or material of monochromating substance. Chemical formula can be specified separately.
    Use the “reflection” field to indicate the (hkl) orientation. Use the “d_spacing” field to
    record the lattice plane spacing.
    """

    chemical_formula: NxField | None = None
    """The chemical formula specified using CIF conventions.
    The chemical formula specified using CIF conventions. Abbreviated
    version of CIF standard.
    """

    order_no: NxField | None = None
    """A number which describes if this is the first, second, n_th, crystal in a multi
    crystal monochromator."""

    cut_angle: NxField | None = None
    """Cut angle of reflecting Bragg plane and plane of crystal surface."""

    space_group: NxField | None = None
    """Space group of crystal structure."""

    unit_cell: NxField | None = None
    """Unit cell parameters (lengths and angles)."""

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
    """Orientation matrix of single crystal sample using Busing-Levy convention:
    W. R. Busing and H. A. Levy (1967). Acta Cryst. 22, 457-464"""

    wavelength: NxField | None = None
    """Optimum diffracted wavelength."""

    d_spacing: NxField | None = None
    """Spacing between crystal planes of the reflection."""

    scattering_vector: NxField | None = None
    """Scattering vector, Q, of nominal reflection."""

    reflection: NxField | None = None
    """Miller indices (hkl) values of nominal reflection."""

    thickness: NxField | None = None
    """Thickness of the crystal. (Required for Laue orientations - see “usage” field)."""

    density: NxField | None = None
    """Mass density of the crystal."""

    segment_width: NxField | None = None
    """Horizontal width of individual segment."""

    segment_height: NxField | None = None
    """Vertical height of individual segment."""

    segment_thickness: NxField | None = None
    """Thickness of individual segment."""

    segment_gap: NxField | None = None
    """Typical gap between adjacent segments."""

    segment_columns: NxField | None = None
    """Number of segment columns in horizontal direction."""

    segement_rows: NxField | None = None
    """Number of segment rows in vertical direction."""

    mosaic_horizontal: NxField | None = None
    """Horizontal mosaic Full Width Half Maximum."""

    mosaic_vertical: NxField | None = None
    """Vertical mosaic Full Width Half Maximum."""

    curvature_horizontal: NxField | None = None
    """Horizontal curvature of focusing crystal."""

    curvature_vertical: NxField | None = None
    """Vertical curvature of focusing crystal."""

    is_cylindrical: NxField | None = None
    """Is this crystal bent cylindrically?"""

    cylindrical_orientation_angle: NxField | None = None
    """If cylindrical: cylinder orientation angle."""

    # Purposfully ommiting `polar_angle` and `azimuthal_angle` as NXtransformations
    # are preferred.

    bragg_angle: NxField | None = None
    """Bragg angle of nominal reflection."""

    temperature: NxField | None = None
    """Average/nominal crystal temperature."""

    temperature_coefficient: NxField | None = None
    """How lattice parameter changes with temperature."""

    depends_on: NxField | None = None
    """Add a definition for the reference point of a crystal."""

    temperature_log: NxLog | None = None
    """log file of crystal temperature."""

    reflectivity: NxData | None = None
    """Crystal reflectivity versus wavelength."""

    transmission: NxData | None = None
    """Crystal transmission versus wavelength."""
