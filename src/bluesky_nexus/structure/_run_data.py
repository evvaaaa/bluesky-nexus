"""Contains dataclasses which represent all the necessary data required by
the ``create_nexus_structure``.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from event_model import (
    EventDescriptor,
    PerObjectHint,
    RunStart,
    RunStop,
)
from event_model.documents.event_descriptor import Dtype, DtypeNumpy, DtypeNumpyItem


def sanitize_datakey_for_nexus(data_key: str) -> str:
    """NeXus doesn't allow underscores in keys.

    To be safe we make sure a given datakey is alphanumeric.
    """
    return re.sub(r"[^A-Za-z0-9_]", "", data_key.replace("-", "_"))


@dataclass
class DataKeyData:
    dtype: Dtype
    """The data_key dtype."""

    dtype_numpy: DtypeNumpy | list[DtypeNumpyItem] | None
    """The data_key numpy dtype, if defined."""

    data: list[Any]
    """Data measured for this data_key."""

    timestamps: list[float]
    """Timestamps measured for this data_key"""

    units: str | None
    """The units for this data_key received through the descriptor."""


@dataclass
class ObjectData:
    raw_nx_schema: dict | None
    """The nexus schema for this object as a dictionary."""

    data_key_name_to_data: dict[str, DataKeyData]
    """A dictionary of data key name to data key/configuration key information."""

    formatted_data_key_name_to_data: dict[str, DataKeyData]
    """A dictionary of nx data key name to data key/configuration key information."""

    separator: str | None = None
    """The separator being used in this device."""

    hint: PerObjectHint | None = None
    """The hint of the device."""


@dataclass
class StreamData:
    descriptor: EventDescriptor
    """The full event descriptor."""

    stream_start_time: float
    """The timestamp of the first descriptor of the stream."""

    sequence_numbers: list[int] = field(default_factory=list)
    """The sequence number of each event in the stream."""

    times: list[float] = field(default_factory=list)
    """The timestamp of each event in the stream."""

    object_data: dict[str, ObjectData] = field(default_factory=dict)
    """A dictionary of object_key to data stored throughout the experiment."""


@dataclass
class RunData:
    run_start: RunStart
    """The full run start."""

    start_time: float
    """The timestamp of the run start of the plan."""

    stream_name_to_stream_data: dict[str, StreamData] = field(default_factory=dict)
    """A dictionary of stream name to data parsed from that stream."""

    descriptor_uid_to_stream_name: dict[str, str] = field(default_factory=dict)
    """A dictionary of descriptor uid to descriptor stream name."""

    run_stop: RunStop | None = None
    """The full run stop document."""
