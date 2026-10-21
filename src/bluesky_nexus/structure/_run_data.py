"""Contains dataclasses which represent all the necessary data required by
the ``create_nexus_structure``.
"""

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, cast

from bluesky.protocols import Descriptor
from event_model import (
    Configuration,
    DataKey,
    Event,
    EventDescriptor,
    EventPage,
    PerObjectHint,
    RunStart,
    RunStop,
)
from event_model.documents.event_descriptor import Dtype, DtypeNumpy, DtypeNumpyItem

from bluesky_nexus.logger import LOGGER
from bluesky_nexus.schema import (
    NxBaseClass,
    NxField,
    NxGroup,
)


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

    data: list[Any]
    """Data measured for this data_key."""

    timestamps: list[float]
    """Timestamps measured for this data_key"""

    units: str | None
    """The units for this data_key received through the descriptor."""


@dataclass
class ObjectData:
    nx_schema: NxGroup | NxField
    """The nexus schema for this object."""
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
    stream_start_time: float
    object_data: dict[str, ObjectData] = field(default_factory=dict)
    """A dictionary of object_key to data stored throughout the experiment."""

    sequence_numbers: list[int] = field(default_factory=list)
    times: list[float] = field(default_factory=list)


@dataclass
class RunData:
    run_start: RunStart
    start_time: float
    stream_name_to_stream_data: dict[str, StreamData] = field(default_factory=dict)
    descriptor_uid_to_stream_name: dict[str, str] = field(default_factory=dict)

    run_stop: RunStop | None = None
