"""NeXus Writer callback for bluesky plans."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from importlib.metadata import version
from typing import Any, cast

from event_model import (
    Configuration,
    DataKey,
    Event,
    EventDescriptor,
    EventPage,
    PerObjectHint,
    RunStop,
    documents,
)
from event_model.documents import Document, RunStart
from nexusformat import nexus

from bluesky_nexus.logger import LOGGER
from bluesky_nexus.schema import NxBaseClass, NxField, NxGroup
from bluesky_nexus.structure import (
    DataKeyData,
    ObjectData,
    RunData,
    StreamData,
    create_nexus_structure,
    sanitize_datakey_for_nexus,
)

__version__ = version("bluesky_nexus")


def _add_lists_mutably(list1: list, list2: list) -> None:
    list1 += list2


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

    return NxBaseClass.from_dictionary(raw_schema)


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


def _object_data_from_descriptor_data(
    object_name: str,
    hint: PerObjectHint,
    read_data_keys: dict[str, DataKey],
    configuration: Configuration,
) -> ObjectData:
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
            # TODO: Move this logic into `create_structure`.
            nx_schema = NxGroup.from_dictionary(raw_schema)

            # Fill the specified schema with the keys which
            # weren't specified.
            nx_schema = new_schema_with_missing_fields(formatted_data_key_name_to_data, nx_schema)
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


def _append_event_or_event_page(
    stream_data: StreamData, document: Event | EventPage, operation: Callable[[list, Any], None]
) -> None:
    operation(stream_data.sequence_numbers, document["seq_num"])

    operation(stream_data.times, document["time"])

    # Intentionally not deep copied to keep mutable references to data.
    event_data = document["data"].copy()
    event_timestamps = document["timestamps"].copy()

    for object_data in stream_data.object_data.values():
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


class BlueskyNexusCallback(ABC):
    """Callback that builds a new NeXus NXroot per plan and passes it to
    process_nexus_structure."""

    def __init__(self) -> None:
        """Initialize the NeXus callback and save consumers."""
        # Log the version of the package
        LOGGER.info(f"NexusCallback Initialized: version - {__version__}")
        self._run_data: RunData | None = None

    def __call__(self, name: str, document: Document) -> None:
        """Extract the nexus and detector information throughtout the run
        and then produce a file on run_stop.
        """
        if name == "start":
            self.run_start(document)  # type: ignore
        if name == "descriptor":
            self.descriptor(document)  # type: ignore
        elif name == "event":
            self.event(document)  # type: ignore
        elif name == "event_page":
            self.event_page(documents)  # type: ignore
        elif name == "stop":
            self.run_stop(document)  # type: ignore

    def descriptor(self, document: EventDescriptor) -> None:
        """Fill the existing `RunData` with descriptor data."""
        if self._run_data is None:
            LOGGER.warning("Received descriptor without a run start...")
            return

        stream_name = document["name"]  # type: ignore
        self._run_data.descriptor_uid_to_stream_name[document["uid"]] = stream_name  # type: ignore

        if (
            (existing_stream_data := self._run_data.stream_name_to_stream_data.get(stream_name))  # type: ignore
            and document["run_start"] == self._run_data.run_start["uid"]
        ):  # type: ignore
            # There was a redeclare on the stream. Add to the existing configuration.
            for object_name in cast(dict, document.get("object_keys", {})):
                configuration = cast(
                    PerObjectHint,
                    document.get("configuration", {}).get(object_name, {}),  # type: ignore
                )
                if object_name in existing_stream_data.object_data:
                    object_data = existing_stream_data.object_data[object_name]
                    for (
                        data_key_name,
                        data_key_data,
                    ) in object_data.data_key_name_to_data.items():
                        configuration_data = cast(dict, configuration.get("data", {}))
                        configuration_timestamps = cast(dict, configuration.get("timestamps", {}))
                        if data_key_name in configuration_data:
                            data_key_data.data.append(configuration_data[data_key_name])
                            data_key_data.timestamps.append(configuration_timestamps[data_key_name])

        else:
            # Make a new stream.
            object_data = {}
            # Parse all the objects into their own objects containing their data keys.
            for object_name, data_key_names in document.get("object_keys", {}).items():
                data_keys = {k: v for k, v in document["data_keys"].items() if k in data_key_names}
                configuration = document.get("configuration", {}).get(object_name, {})
                hint = document.get("hints", {}).get(object_name, {})
                object_data[object_name] = _object_data_from_descriptor_data(
                    object_name,
                    cast(PerObjectHint, hint),
                    data_keys,
                    configuration,
                )

            self._run_data.stream_name_to_stream_data[stream_name] = StreamData(
                document,
                document["time"],
                object_data=dict(sorted(object_data.items(), reverse=True)),
            )

    def event(self, document: Event) -> None:
        """Extracts an event into the ``StreamData`` it's referencing."""

        if self._run_data is None:
            LOGGER.warning("Received event without a run start...")
            return

        stream_name = self._run_data.descriptor_uid_to_stream_name.get(document["descriptor"])
        if stream_name is None:
            LOGGER.warning(
                "Received event for stream that wasn't processed. Continuing without it..."
            )
            return
        stream_data = self._run_data.stream_name_to_stream_data[stream_name]
        _append_event_or_event_page(stream_data, document, list.append)

    def event_page(self, document: EventPage) -> None:
        """Extracts an event page into the ``StreamData`` it's referencing."""

        if self._run_data is None:
            LOGGER.warning("Received event_page without a run start...")
            return

        stream_name = self._run_data.descriptor_uid_to_stream_name.get(document["descriptor"])
        if stream_name is None:
            LOGGER.warning(
                "Received event page for stream that wasn't processed. Continuing without it..."
            )
            return
        stream_data = self._run_data.stream_name_to_stream_data[stream_name]
        _append_event_or_event_page(stream_data, document, _add_lists_mutably)

    def run_start(self, document: RunStart) -> None:
        """Create a parser for capturing run information."""
        self._run_data = RunData(document, document["time"])

    def run_stop(self, document: RunStop) -> None:
        """Create and return the nexus structure for the plan."""
        if self._run_data is None:
            return
        self._run_data.run_stop = document  # type: ignore

        nexus_structure = create_nexus_structure(self._run_data)
        self.process_nexus_structure(nexus_structure)

    @abstractmethod
    def process_nexus_structure(self, generated_structure: nexus.NXroot) -> Any:
        """Abstract method where the nexus structure generated through this callback
        can be processed in subclasses. For an example see `NexusHdfWriterCallback`."""
