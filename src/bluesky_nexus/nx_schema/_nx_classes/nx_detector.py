"""Contains the definition for `NXdetector`."""

from ..nx_base import NxField, NxGroup, add_nx_class_basemodel


@add_nx_class_basemodel
class NxDetector(NxGroup):
    """Represents a NeXus detector."""

    data: NxField
    # TODO: Add the others
