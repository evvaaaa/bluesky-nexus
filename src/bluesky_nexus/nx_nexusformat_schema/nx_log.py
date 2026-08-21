"""Contains the definition for NXlog."""

from bluesky_nexus.nx_schema import (
    NxAttribute,
    NxField,
    add_nx_class_basemodel,
)

from .nx_object import NxObject


class NxTimeField(NxField):
    start: NxAttribute | None = None
    """Times in this log field are given relative to this start attribute."""


class NxLogTimeField(NxTimeField):
    scaling_factor: NxAttribute | None = None
    """Applied to the time values in order to arrive at the units specified in the units attribute.
    of this field. This allows for arbitrary time units such as ticks of some hardware clock."""


@add_nx_class_basemodel
class NxLog(NxObject):
    """Represents a NeXus NXlog."""

    time: NxLogTimeField | None = None
    """Time of logged entry."""

    value: NxLogTimeField | None = None
    """Array of logged value, such as temperature. If this is a single value the dimensionality is
    nEntries. However, NXlog can also be used to store multi dimensional time stamped data such
    as images. In this example the dimensionality of values would be value[nEntries,xdim,ydim].
    """

    raw_value: NxField | None = None
    """Array of raw information, such as thermocouple voltage"""

    description: NxField | None = None
    """Description of logged value."""

    average_value: NxField | None = None
    """The average value of the value field."""

    average_value_errors: NxField | None = None
    """Estimated uncertainty (often used: standard deviation) of average_value."""

    minimum_value: NxField | None = None
    """Minimum value of the value field."""

    maximum_value: NxField | None = None
    """Maximum value of the value field."""

    duration: NxField | None = None
    """Total time log was taken."""

    cue_index: NxField | None = None
    """Index into the time, value pair matching the corresponding cue_timestamp_zero."""

    cue_timestamp_zero: NxLogTimeField | None = None
    """Timestamps matching the corresponding cue_index into the time, value pair."""
