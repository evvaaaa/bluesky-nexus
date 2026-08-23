"""Contains the definition for NXcomponent."""

from bluesky_nexus.base_schema import NxField, add_nx_class_basemodel

from .nx_object import NxObject


@add_nx_class_basemodel
class NxComponent(NxObject):
    """Represents a NeXus NXcomponent.

    Base class for components of an instrument - real ones or simulated ones.

    Additional fields of NXfabrication, NXprogram, and NXtransformations are expected.
    """

    applied: NxField | None = None
    """Was the component used?"""

    name: NxField | None = None
    """Name of the component."""

    description: NxField | None = None
    """Ideally, use instances of identifierNAME to point to a resource that
    provides further details. If such a resource does not exist or should not
    be used, use this free text, although it is not recommended.
    """

    inputs: NxField | None = None
    """Instance or list of instances of NXcomponent (or base classes extending NXcomponent)
    or NXbeam that act as input(s) to this component.
    Each input should point to the path of the group acting as input.
    """

    outputs: NxField | None = None
    """Instance or list of instances of NXcomponent (or base classes extending NXcomponent)
    or NXbeam that act as output(s) of this component."""

    depends_on: NxField | None = None
    """Specifies the position of the component by pointing to the last transformation in the
    transformation chain that is defined via the NXtransformations group."""
