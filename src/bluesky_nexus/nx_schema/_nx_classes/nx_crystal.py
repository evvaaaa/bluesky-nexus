"""Contains the definition for NXcrystal."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_component import NxComponent


@add_nx_class_basemodel
class NxCrystal(NxComponent):
    """Represents a NeXus NXcrystal."""

    usage: NxField | None = None
    """How this crystal is used. Choices are in the list.
    Either "Bragg" or "Laue"
    """

    type: NxField | None = None
    """Type or material of monochromating substance. Chemical formula can be specified separately.
    Use the “reflection” field to indicate the (hkl) orientation. Use the “d_spacing” field to
    record the lattice plane spacing.
    """

    chemical_formula: NxField | None = None
    """The chemical formula specified using CIF conventions.
    The chemical formula specified using CIF conventions. Abbreviated version of CIF standard
    """
