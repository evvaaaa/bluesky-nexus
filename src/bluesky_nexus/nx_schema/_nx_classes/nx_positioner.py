"""Contains the definition for NXpositioner."""

from .._nx_base import NxField, add_nx_class_basemodel
from .nx_component import NxComponent


@add_nx_class_basemodel
class NxPositioner(NxComponent):
    """Represents a NeXus NXpositioner."""

    value: NxField | None = None
    """best known value of positioner."""

    raw_value: NxField | None = None
    """raw value of positioner."""

    target_value: NxField | None = None
    """target value of positioner."""

    tolerance: NxField | None = None
    """maximum allowable difference between target_value and value."""

    soft_limit_min: NxField | None = None
    """minimum allowed limit to set value."""

    soft_limit_max: NxField | None = None
    """maximum allowed limit to set value."""

    velocity: NxField | None = None
    """velocity of the positioner (distance moved per unit time)"""

    acceleration_time: NxField | None = None
    """time to ramp the velocity up to full speed"""

    controller_record: NxField | None = None
    """Hardware device record, e.g. EPICS process variable, taco/tango …"""
