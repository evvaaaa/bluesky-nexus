"""Contains a classes which represent all the necessary data required by
the nexus writer. This is collected throughout the run. The writer will then use the
RunData to write to disk.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, cast

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

from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.nx_schema import NxField, NxGroup, NxObject
from bluesky_nexus.nx_schema.hint_structure import (
    NxFieldInHints,
    PerObjectHintWithSchemaField,
)
from bluesky_nexus.nx_schema.nx_base import DISALLOWED_ALIASES_AND_OBJECT_NAMES, NxBase


def _add_lists_mutably(list1: list, list2: list) -> None:
    list1 += list2


@dataclass
class DataKeyData:
    dtype: Dtype
    """The datakey dtype."""

    dtype_numpy: DtypeNumpy | list[DtypeNumpyItem] | None

    data: list[Any]
    """Data measured for this datakey."""

    timestamps: list[float]
    """Timestamps measured for this datakey"""

    units: str | None
    """The units for this datakey received through the descriptor."""


def _new_schema_with_missing_fields(
    object_name: str,
    data_key_data: dict[str, DataKeyData],
    nx_schema: NxGroup,
) -> NxGroup:
    # Add units specified in the schema if not provided through the descriptor.
    fields_specified_in_schema = {
        nx_field.datakey: nx_field for nx_field in nx_schema.all_nx_fields().values()
    }

    raw_schema = nx_schema.model_dump()
    for nx_field in fields_specified_in_schema.values():
        if (
            (data_key := data_key_data.get(nx_field.datakey))
            and nx_field.nx_units is None
            and data_key.units is not None
        ):  # Add the units
            data_key.units = nx_field.nx_units

    for data_key_name, data_key_datum in data_key_data.items():
        if data_key_name not in fields_specified_in_schema:
            prospective_alias = (
                (data_key_name.lstrip(object_name).lstrip("-").lstrip("_"))
                if data_key_name != object_name
                else object_name
            )
            if prospective_alias in DISALLOWED_ALIASES_AND_OBJECT_NAMES:
                # The datakey with the object name stripped is not valid.
                logger.warning(
                    f"Automatically added datakey {data_key_name} cannot be given"
                    f"the alias {prospective_alias} because it is disallowed. "
                    "It will be skipped..."
                )
                continue

            raw_schema[prospective_alias] = NxFieldInHints(
                nx_class="NXfield",
                datakey=data_key_name,
                nx_alias=prospective_alias,
                nx_units=data_key_datum.units,
            )
    return NxGroup.from_dict(raw_schema)


@dataclass
class ObjectData:
    nx_schema: NxBase
    """The nexus schema for this object."""
    data_key_data: dict[str, DataKeyData] = field(default_factory=dict)
    """A dictionary of datakey name to data key/configuration key information."""

    @classmethod
    def from_descriptor_data(
        cls,
        object_name: str,
        hint: PerObjectHintWithSchemaField,
        data_keys: dict[str, DataKey],
        configuration: Configuration | None,
    ) -> "ObjectData":
        configuration = configuration or {}
        data_key_data: dict[str, DataKeyData] = {}

        # Parse datakeys + data from configuration.
        for data_key_name, data_key_value in configuration.get("data_keys", {}).items():
            if "data" in configuration:
                units = data_key_value.get("units")
                dtype = configuration["data_keys"][data_key_name]["dtype"]  # type: ignore
                dtype_numpy = configuration["data_keys"][data_key_name].get(
                    "dtype_numpy"
                )  # type: ignore
                # Will always be a singleton list so that we can reuse all the
                # event datakey code in the writer.
                data = [configuration["data"][data_key_name]]  # type: ignore
                timestamps = [
                    configuration["timestamps"][data_key_name]  # type: ignore
                ]

                data_key_data[data_key_name] = DataKeyData(
                    units=units,
                    dtype=dtype,
                    dtype_numpy=dtype_numpy,
                    data=data,
                    timestamps=timestamps,
                )

        # Parse datakeys which will be read in the stream through events.
        for data_key_name, data_key_value in data_keys.items():
            if data_key_name in data_key_data:
                logger.warning(
                    f"Received datakey {data_key_name} in for a configuration "
                    "datakey as well as a standard one, weird device you got there! "
                    "The writer will use the standard data one."
                )

            if data_key_name in DISALLOWED_ALIASES_AND_OBJECT_NAMES:
                logger.warning(
                    f"datakey {data_key_data} is not a valid datakey "
                    "name in the writer. it will be skipped."
                )
                continue
            units = data_key_value.get("units")
            dtype = data_key_value["dtype"]
            dtype_numpy = data_key_value.get("dtype_numpy")  # type: ignore
            data_key_data[data_key_name] = DataKeyData(
                units=units,
                dtype=dtype,
                dtype_numpy=dtype_numpy,
                data=[],
                timestamps=[],
            )

        # Parse the nexus schema or make a new NXobject, add the missing keys
        # (if possible)
        if "NX_schema" in hint:
            # Only validate with NxGroup to ensure maximum campatibility with packages
            # adding their own schema in the device layer.
            # If a device passes validation on `NxGroup` it can be added
            try:
                raw_schema = hint["NX_schema"]
                validated_user_defined = NxBase.from_dict(cast(dict, raw_schema))
                validated_after_exchanges = validated_user_defined.patch_object_keys(
                    object_name
                )
                nx_schema = (
                    _new_schema_with_missing_fields(
                        object_name, data_key_data, validated_after_exchanges
                    )
                    if isinstance(validated_after_exchanges, NxGroup)
                    else validated_after_exchanges
                    # If the object is an `nx_class` NXfield in the yaml directly.
                )
                return ObjectData(nx_schema=nx_schema, data_key_data=data_key_data)

            except Exception as exception:
                logger.warning(
                    f"Received a malformed schema in {object_name}. "
                    f"The error was:\n    {str(exception)}\n"
                    "A default schema will be used instead.",
                )

        if len(data_key_data) == 1:
            # The device has a single field. Don't make it an `NXobject`.
            # This is very likely if the plan throws in one signal from a device.
            only_key = list(data_key_data)[0]
            logger.debug(f"Creating new NxField schema for device {object_name}.")
            return ObjectData(
                nx_schema=NxField(datakey=only_key), data_key_data=data_key_data
            )
        else:
            nx_schema = NxObject()
            nx_schema = _new_schema_with_missing_fields(
                object_name, data_key_data, nx_schema
            )
            logger.debug(f"Creating new NxObject schema for device {object_name}.")
        return ObjectData(nx_schema=nx_schema, data_key_data=data_key_data)


@dataclass
class StreamData:
    object_data: dict[str, ObjectData] = field(default_factory=dict)
    """A dictionary of object_key to data stored throughout the experiment."""

    sequence_numbers: list[int] = field(default_factory=list)
    read_times: list[float] = field(default_factory=list)

    DISALLOWED_OBJECT_NAMES = frozenset(["read_times"])
    """Keys which can't be selected because they're used to store information
    about the stream."""

    @classmethod
    def from_descriptor(cls, descriptor: EventDescriptor) -> "StreamData":
        """Parse descriptor into individual object data."""
        object_data = {}
        # Sort so that longer datakeys are first.
        # When we pull data out of events all the datakeys will be flat.
        # We'll parse e.g "some-device" first (earlier in this list) before we parse
        # e.g "some-dev".
        for object_name, data_key_names in descriptor.get("object_keys", {}).items():
            if object_name in cls.DISALLOWED_OBJECT_NAMES:
                logger.warning(
                    f"Received an object called {object_name}. "
                    "This is disallowed in the nexus writer. "
                    "The device will be skipped..."
                )
            data_keys = {
                k: v for k, v in descriptor["data_keys"].items() if k in data_key_names
            }
            configuration = descriptor.get("configuration", {}).get(object_name, {})
            hint = descriptor.get("hints", {}).get(object_name, {})
            object_data[object_name] = ObjectData.from_descriptor_data(
                object_name,
                cast(PerObjectHintWithSchemaField, hint),
                data_keys,
                configuration,
            )

        return StreamData(object_data=dict(sorted(object_data.items(), reverse=True)))

    def reconfigure(self, descriptor: Descriptor):
        """
        Append data from a second descriptor of a stream into existing
        configuration.
        """
        for object_name in cast(dict, descriptor.get("object_keys", {})):
            if object_name in self.DISALLOWED_OBJECT_NAMES:
                logger.warning(
                    f"Received an object called {object_name}. "
                    "This is disallowed in the nexus writer. "
                    "The device will be skipped..."
                )

            configuration = cast(
                PerObjectHint,
                descriptor.get("configuration", {}).get(object_name, {}),  # type: ignore
            )
            if object_name in self.object_data:
                object_datum = self.object_data[object_name]
                for data_key_name, data_key_data in object_datum.data_key_data.items():
                    configuration_data = cast(dict, configuration.get("data", {}))
                    configuration_timestamps = cast(
                        dict, configuration.get("timestamps", {})
                    )
                    if data_key_name in configuration_data:
                        data_key_data.data.append(configuration_data[data_key_name])
                        data_key_data.timestamps.append(
                            configuration_timestamps[data_key_name]
                        )

    def _extract_event_or_event_page(
        self, document: Event | EventPage, operation: Callable[[list, Any], None]
    ) -> None:
        event_data = document.get("data", {})
        event_timestamps = document.get("timestamps", {})

        operation(self.sequence_numbers, document["seq_num"])

        operation(self.read_times, document["time"])

        # Intensionally not deep copied to keep mutable reference#
        event_data = document["data"].copy()
        event_timestamps = document["timestamps"].copy()

        for object_name in self.object_data:
            for data_key_name, timestamp in event_timestamps.items():
                if data_key_name.startswith(object_name):
                    # Popping so other shorter object keys don't
                    # get attributes to the longer, similarly named
                    # objects.
                    data = event_data.pop(data_key_name)
                    operation(
                        self.object_data[object_name].data_key_data[data_key_name].data,
                        data,
                    )
                    operation(
                        self.object_data[object_name]
                        .data_key_data[data_key_name]
                        .timestamps,
                        timestamp,
                    )
            event_timestamps = {
                k: v for k, v in event_timestamps.items() if k in event_data
            }  # Filter already seen and removed datakeys.

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

    DISALLOWED_STREAM_NAMES = frozenset(["run_info"])
    run_stop: RunStop | None = None

    """Not permitted stream names. Run info is where the start and
    stop docs are stored."""

    def extract_descriptor(self, descriptor: EventDescriptor) -> None:
        stream_name = descriptor["name"]  # type: ignore
        if stream_name in self.DISALLOWED_STREAM_NAMES:
            logger.warning(
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
        stream_name = self.descriptor_uid_to_stream_name.get(event["descriptor"])
        if stream_name is None:
            logger.warning(
                "Received event for stream that wasn't processed. "
                "Continuing without it..."
            )
            return
        self.stream_name_to_stream_data[stream_name].extract_event(event)

    def extract_event_page(self, event_page: EventPage) -> None:
        stream_name = self.descriptor_uid_to_stream_name.get(event_page["descriptor"])
        if stream_name is None:
            logger.warning(
                "Received event page for stream that wasn't processed. "
                "Continuing without it..."
            )
            return
        self.stream_name_to_stream_data[stream_name].extract_event_page(event_page)
