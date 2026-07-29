"""Contains a classes which represent all the necessary data required by
the nexus writer. This is collected throughout the run. The writer will then use the
RunData to write to disk.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, cast

from event_model import (
    Configuration,
    DataKey,
    Event,
    EventDescriptor,
    EventPage,
    RunStart,
    RunStop,
)

from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.schema import NxBase, NxObject
from bluesky_nexus.schema._base_schema import DISALLOWED_ALIASES_AND_OBJECT_NAMES
from bluesky_nexus.schema.hint_structure import (
    NxField,
    PerObjectHintWithSchemaField,
)


def _add_lists_mutably(list1: list, list2: list) -> None:
    list1 += list2


@dataclass
class DataKeyData:
    data: list[Any] = field(default_factory=list)
    """Data measured for this datakey."""

    timestamps: list[float] = field(default_factory=list)
    """Timestamps measured for this datakey"""

    units: str | None = None
    """The units for this datakey received through the descriptor."""


def _new_schema_with_missing_fields(
    object_name: str, data_key_data: dict[str, DataKeyData], schema: NxBase
) -> NxBase:
    # Add units specified in the schema if not provided through the descriptor.
    fields_specified_in_schema = schema.all_nx_fields()

    raw_schema = schema.model_dump()
    for nx_field in fields_specified_in_schema:
        if (
            data_key := data_key_data.get(nx_field.datakey, None)
        ) and data_key.units is None:
            data_key.units = nx_field.nx_units

    for data_key_name, data_key_datum in data_key_data.items():
        if data_key_name not in fields_specified_in_schema:
            prospective_alias = (
                data_key_name.lstrip(object_name).lstrip("-").lstrip("_")
            )
            if prospective_alias in DISALLOWED_ALIASES_AND_OBJECT_NAMES:
                # The datakey with the object name stripped is not valid.
                logger.warning(
                    f"Automatically added datakey {data_key_name} cannot be given"
                    f"the alias {prospective_alias} because it is disallowed. "
                    "It will be skipped..."
                )

            raw_schema[data_key_name] = NxField(
                nx_alias=prospective_alias, nx_units=data_key_datum.units
            )

    return NxBase.from_dict(raw_schema)


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
            new_configuration_data_key_data = DataKeyData()
            new_configuration_data_key_data.units = data_key_value.get("units")
            # Will always be a singleton list so that we can reuse all the
            # event datakey code in the writer.
            if "data" in configuration:
                new_configuration_data_key_data.data = [
                    configuration["data"][data_key_name]
                ]  # type: ignore
                new_configuration_data_key_data.timestamps = [
                    configuration["timestamps"][data_key_name]  # type: ignore
                ]
            else:
                # Pretty sure this can never happen... but if we don't receive
                # data in the descriptor (what the document model suggests, then
                # just skip it but keep an empty list.)
                new_configuration_data_key_data.data = []
                new_configuration_data_key_data.timestamps = []

            data_key_data[data_key_name] = new_configuration_data_key_data

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
            new_data_key_data = DataKeyData()
            new_data_key_data.units = data_key_value.get("units")
            data_key_data[data_key_name] = new_data_key_data

        # Parse the nexus schema or make a new NXobject, add the missing keys
        # (if possible)
        if "NX_schema" in hint:
            # Only validate with NxBase to ensure maximum campatibility with packages
            # adding their own schema in the device layer.
            # If a device passes validation on `NxBase` it can be added
            try:
                raw_schema = hint["NX_schema"]
                validated_user_defined = NxBase.from_dict(cast(dict, raw_schema))
                validated_after_exchanges = validated_user_defined.patch_object_keys(
                    object_name
                )
                nx_schema = _new_schema_with_missing_fields(
                    object_name, data_key_data, validated_after_exchanges
                )
                return ObjectData(nx_schema=nx_schema, data_key_data=data_key_data)

            except Exception as _:
                logger.warning(
                    f"Received a malformed schema in {object_name}."
                    "A default schema will be used instead.",
                    exc_info=True,
                )
        # Used in the case of an exception above, or if the device doesn't
        # come with a schema.
        raw_schema = NxObject()  # type: ignore
        nx_schema = _new_schema_with_missing_fields(
            object_name, data_key_data, raw_schema
        )
        logger.debug(f"Creating new NxObject schema for device {object_name}.")
        return ObjectData(nx_schema=nx_schema, data_key_data=data_key_data)


@dataclass
class StreamData:
    object_data: dict[str, ObjectData] = field(default_factory=dict)
    """A dictionary of object_key to data stored throughout the experiment."""

    sequence_numbers: list[int] = field(default_factory=list)
    read_times: list[float] = field(default_factory=list)

    DISALLOWED_OBJECT_NAMES = frozenset(["sequence_numbers", "read_times"])
    """Keys which can't be selected because they're used to store information
    about the stream."""

    @classmethod
    def from_descriptor(cls, descriptor: EventDescriptor) -> "StreamData":
        """Parse descriptor into individual object data."""
        object_data = {}
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

        # Sort so that longer datakeys are first.
        # When we pull data out of events all the datakeys will be flat.
        # We'll parse e.g "some-device" first (earlier in this list) before we parse
        # e.g "some-dev".
        return StreamData(object_data=dict(sorted(object_data.items(), reverse=True)))

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
        new_stream_data_extractor = StreamData.from_descriptor(descriptor)
        self.stream_name_to_stream_data[descriptor["name"]] = new_stream_data_extractor  # type: ignore

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
