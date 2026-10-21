"""Contains dataclasses which represent all the necessary data required by
the ``create_nexus_structure``.

This is collected throughout the run. Filtering out event data into
these dataclasses greatly improves readability.
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

# from bluesky_nexus.nexusformat_schema import NxSubEntry


def _add_lists_mutably(list1: list, list2: list) -> None:
    list1 += list2


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


def new_schema_with_missing_fields(
    data_key_data: dict[str, DataKeyData],
    nx_schema: NxGroup,
) -> NxGroup:
    """Takes a nexus schema and data keys for an object. If the data key
    isn't present in the schema then try adding them and validating again.
    """
    nx_alias_to_nx_field = nx_schema.all_nx_fields()

    schema_specified_data_keys = {
        nx_field.data_key: nx_field for nx_field in nx_alias_to_nx_field.values()
    }

    raw_schema = nx_schema.model_dump()

    for data_key_name in data_key_data:
        if schema_specified_data_keys.get(data_key_name):
            continue  # Already added manually.

        raw_schema[sanitize_datakey_for_nexus(data_key_name)] = {
            "data_key": data_key_name,
        }

    return NxGroup.from_dictionary(raw_schema)


def _separator_from_data_keys(
    object_name: str,
    data_key_names: Iterable[str],
) -> str | None:
    """For a given `object_name` and datakeys in that object, attempt to find
    the name separator in those datakeys. If `None` then there is no
    separator, e.g the device doesn't have heirarchical naming."""

    # Add units specified in the schema if not provided through the descriptor.
    separator: str | None = None
    for data_key_name in data_key_names:
        stripped_of_object_name = data_key_name.removeprefix(object_name)
        if stripped_of_object_name == "":
            # We've found a data_key equal to the object name,
            # like on a PV positioner.
            continue
        separator = stripped_of_object_name[0]
        break
    return separator


def _data_key_to_nx_formatted_data_key(
    data_key_name: str, object_name: str, separator: str | None
) -> str:
    """Takes a given data key name and give back how it would be specified
    in the nexus schema."""
    if data_key_name == object_name:
        return ""
    return data_key_name.removeprefix(object_name).removeprefix(separator or "")


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

    @classmethod
    def from_descriptor_data(
        cls,
        object_name: str,
        hint: PerObjectHint,
        read_data_keys: dict[str, DataKey],
        configuration: Configuration,
    ) -> "ObjectData":
        """Parse object information from the descriptor into pertinant information about
        an object."""
        configuration_data_keys: dict[str, DataKey] = configuration.get("data_keys", {})
        # Check for common elements in configuration and read data keys.
        # In practice the user won't do this, but it's allowed in event-model.
        if common := list(configuration_data_keys.keys() & read_data_keys.keys()):
            LOGGER.warning(
                f"Received data_keys {common} in both configuration and "
                "read data_keys. The writer will use the read data key."
            )
        all_data_keys = configuration_data_keys.copy()
        all_data_keys.update(read_data_keys)

        separator = _separator_from_data_keys(object_name, all_data_keys)

        data_key_name_to_data: dict[str, DataKeyData] = {}
        formatted_data_key_name_to_data: dict[str, DataKeyData] = {}

        # Parse all the data_key data.
        for data_key_name, data_key_value in all_data_keys.items():
            units = data_key_value.get("units")
            dtype = data_key_value["dtype"]  # type: ignore
            dtype_numpy = data_key_value.get(  # type: ignore
                "dtype_numpy"
            )
            if data_key_name in configuration_data_keys and data_key_name not in read_data_keys:
                data = [configuration["data"][data_key_name]]  # type: ignore
                timestamps = [
                    configuration["timestamps"][data_key_name]  # type: ignore
                ]
            else:
                data, timestamps = [], []

            data_key_data = DataKeyData(
                dtype=dtype,
                dtype_numpy=dtype_numpy,
                data=data,
                timestamps=timestamps,
                units=units,
            )
            data_key_name_to_data[data_key_name] = data_key_data
            formatted_data_key_name = _data_key_to_nx_formatted_data_key(
                data_key_name, object_name, separator
            )
            formatted_data_key_name_to_data[formatted_data_key_name] = data_key_data

        # Parse the nexus schema or make a new NXobject, add the missing keys
        # (if possible).
        if isinstance(raw_schema := hint.get("NX_schema"), dict):
            try:
                # Perform an initial validation on the provided schema.
                # This will give back the subclass of NxGroup specified
                # in the serialized schema.
                nx_schema = NxGroup.from_dictionary(raw_schema)

                # Fill the specified schema with the keys which
                # weren't specified.
                nx_schema = new_schema_with_missing_fields(
                    formatted_data_key_name_to_data, nx_schema
                )
                return ObjectData(
                    nx_schema=nx_schema,
                    separator=separator,
                    data_key_name_to_data=data_key_name_to_data,
                    formatted_data_key_name_to_data=formatted_data_key_name_to_data,
                    hint=hint,
                )

            except Exception as exception:
                LOGGER.warning(
                    f"Received a malformed schema in {object_name}. "
                    f"The error was:\n    {exception!s}\n"
                    "A default schema will be used instead.",
                )

        # Make a new schema. This will happen if the device didn't specify an "NX_schema",
        # or if the above raised an exception.
        if len(formatted_data_key_name_to_data) == 1:
            # The device has a single key. Don't make it an `NXobject`.
            # This is very likely if the plan throws in signals of a device,
            # but not the device itself.
            only_key = next(iter(formatted_data_key_name_to_data))
            LOGGER.debug(f"Creating new NxField schema for device {object_name}.")
            return ObjectData(
                nx_schema=NxField(data_key=only_key),
                data_key_name_to_data=data_key_name_to_data,
                formatted_data_key_name_to_data=formatted_data_key_name_to_data,
                separator=separator,
                hint=hint,
            )
        else:
            # # Make an NxSubEntry with all the fields from the data keys.
            nx_schema = NxBaseClass.build("NXsubentry")()
            nx_schema = new_schema_with_missing_fields(formatted_data_key_name_to_data, nx_schema)
            LOGGER.debug(f"Creating new NxSubEntry schema for device {object_name}.")
        return ObjectData(
            nx_schema=nx_schema,
            formatted_data_key_name_to_data=formatted_data_key_name_to_data,
            data_key_name_to_data=data_key_name_to_data,
            separator=separator,
            hint=hint,
        )


@dataclass
class StreamData:
    descriptor: EventDescriptor
    stream_start_time: float
    object_data: dict[str, ObjectData] = field(default_factory=dict)
    """A dictionary of object_key to data stored throughout the experiment."""

    sequence_numbers: list[int] = field(default_factory=list)
    times: list[float] = field(default_factory=list)

    @classmethod
    def from_descriptor(cls, descriptor: EventDescriptor) -> "StreamData":
        """Parse descriptor into individual object data."""
        object_data = {}
        # Parse all the objects into their own objects containing their data keys.
        for object_name, data_key_names in descriptor.get("object_keys", {}).items():
            data_keys = {k: v for k, v in descriptor["data_keys"].items() if k in data_key_names}
            configuration = descriptor.get("configuration", {}).get(object_name, {})
            hint = descriptor.get("hints", {}).get(object_name, {})
            object_data[object_name] = ObjectData.from_descriptor_data(
                object_name,
                cast(PerObjectHint, hint),
                data_keys,
                configuration,
            )

        return StreamData(
            descriptor,
            descriptor["time"],
            object_data=dict(sorted(object_data.items(), reverse=True)),
        )

    def reconfigure(self, descriptor: Descriptor) -> None:
        """
        Append data from a second descriptor of a stream into existing
        configuration.
        """
        for object_name in cast(dict, descriptor.get("object_keys", {})):
            configuration = cast(
                PerObjectHint,
                descriptor.get("configuration", {}).get(object_name, {}),  # type: ignore
            )
            if object_name in self.object_data:
                object_data = self.object_data[object_name]
                for (
                    data_key_name,
                    data_key_data,
                ) in object_data.data_key_name_to_data.items():
                    configuration_data = cast(dict, configuration.get("data", {}))
                    configuration_timestamps = cast(dict, configuration.get("timestamps", {}))
                    if data_key_name in configuration_data:
                        data_key_data.data.append(configuration_data[data_key_name])
                        data_key_data.timestamps.append(configuration_timestamps[data_key_name])

    def _extract_event_or_event_page(
        self, document: Event | EventPage, operation: Callable[[list, Any], None]
    ) -> None:
        operation(self.sequence_numbers, document["seq_num"])

        operation(self.times, document["time"])

        # Intentionally not deep copied to keep mutable references to data.
        event_data = document["data"].copy()
        event_timestamps = document["timestamps"].copy()

        for object_data in self.object_data.values():
            for (
                data_key_name,
                data_key_data,
            ) in object_data.data_key_name_to_data.items():
                if data_key_name not in event_data:
                    continue
                event_datum = event_data.pop(data_key_name)
                event_timestamp = event_timestamps.pop(data_key_name)

                operation(
                    data_key_data.data,
                    event_datum,
                )
                operation(
                    data_key_data.timestamps,
                    event_timestamp,
                )

    def extract_event(self, event: Event) -> None:
        """Extract the event data."""
        # For an event we apoend the single seq num data to our own data parsers.
        self._extract_event_or_event_page(event, list.append)

    def extract_event_page(self, event_page: EventPage) -> None:
        """Extract the event page data."""
        # For an event page we add the list data from the event page to
        # the current list.
        self._extract_event_or_event_page(event_page, _add_lists_mutably)


@dataclass
class RunData:
    run_start: RunStart
    start_time: float
    stream_name_to_stream_data: dict[str, StreamData] = field(default_factory=dict)
    descriptor_uid_to_stream_name: dict[str, str] = field(default_factory=dict)

    run_stop: RunStop | None = None

    # TODO: perhaps we instead add a `streams` field at the entry level?
    # I think it makes for nicer parsing for the scientists too because they
    # will be able to see clearly what is a stream in their file.
    DISALLOWED_STREAM_NAMES = frozenset(["run_info"])
    """Not permitted stream names. Run info is where the start and
    stop docs are stored in the nexus structure."""

    def extract_descriptor(self, descriptor: EventDescriptor) -> None:
        """Extracts a descriptor into ``StreamData``."""
        stream_name = descriptor["name"]  # type: ignore
        if stream_name in self.DISALLOWED_STREAM_NAMES:
            LOGGER.warning(
                f"Received stream name {stream_name} which isn't "
                "permitted in the nexus writer. Continuing without it..."
            )

        self.descriptor_uid_to_stream_name[descriptor["uid"]] = descriptor["name"]  # type: ignore
        if (
            descriptor["name"] in self.stream_name_to_stream_data  # type: ignore
            and descriptor["run_start"] == self.run_start["uid"]
        ):  # type: ignore
            # There was a redeclare on the stream. Add to the existing configuration.
            self.stream_name_to_stream_data[descriptor["name"]].reconfigure(descriptor)  # type: ignore

        else:
            # Make a new stream.
            new_stream_data_extractor = StreamData.from_descriptor(descriptor)
            self.stream_name_to_stream_data[descriptor["name"]] = (  # type:ignore
                new_stream_data_extractor
            )

    def extract_event(self, event: Event) -> None:
        """Extracts an event into the ``StreamData`` it's referencing."""
        stream_name = self.descriptor_uid_to_stream_name.get(event["descriptor"])
        if stream_name is None:
            LOGGER.warning(
                "Received event for stream that wasn't processed. Continuing without it..."
            )
            return
        self.stream_name_to_stream_data[stream_name].extract_event(event)

    def extract_event_page(self, event_page: EventPage) -> None:
        """Extracts an event or event page into the ``StreamData`` it's referencing."""
        stream_name = self.descriptor_uid_to_stream_name.get(event_page["descriptor"])
        if stream_name is None:
            LOGGER.warning(
                "Received event page for stream that wasn't processed. Continuing without it..."
            )
            return
        self.stream_name_to_stream_data[stream_name].extract_event_page(event_page)
