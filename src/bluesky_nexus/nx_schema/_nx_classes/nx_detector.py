"""Contains the definition for NXdetector."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_component import NxComponent


@add_nx_class_basemodel
class NxDetector(NxComponent):
    """Represents a NeXus NXdetector."""

    data: NxField
    # TODO: Add the others

    time_of_flight: NxField | None = None
    """Total time of flight."""
    raw_time_of_flight: NxField | None = None
