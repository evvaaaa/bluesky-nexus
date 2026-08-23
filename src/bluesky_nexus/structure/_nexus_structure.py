"""Contains the method ``create_nexus_structure`` for generating the standard
bluesky-nexus ``NXroot`` from plan data."""

from __future__ import annotations

import time
from collections.abc import Iterable
from enum import Enum
from importlib.metadata import version
from typing import Any, cast

import numpy as np
from nexusformat import nexus

from bluesky_nexus.base_schema import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NxField,
    NxGroup,
)
from bluesky_nexus.base_schema._nx_base_leaf import NxBaseLeaf
from bluesky_nexus.logger import LOGGER
from bluesky_nexus.nexusformat_schema import NxData

from ._data_extractor import (
    DataKeyData,
    ObjectData,
    RunData,
    StreamData,
    sanitize_datakey_for_nexus,
)

__version__ = version("bluesky_nexus")

type JsonSerializableScalar = str | int | bool | float | None
# typing.Union required for future recursive references... annoooooying
type JsonSerializableList = list[JsonSerializableScalar | "JsonSerializableList"]
type JsonSerializableTuple = tuple[JsonSerializableScalar | "JsonSerializableTuple"]
type JsonSerializableDict = dict[
    str,
    JsonSerializableScalar | JsonSerializableList | JsonSerializableTuple | "JsonSerializableDict",
]


def _nested_shape(obj: Any) -> tuple[int, ...] | None:
    """Give the shape tuple if obj is a regular Iterable or scalar, else None."""
    if isinstance(obj, str) or not isinstance(obj, Iterable):
        return ()
    obj = list(obj)
    if len(obj) == 0:
        return (0,)
    child_shapes = [_nested_shape(ch) for ch in obj]
    if any(s is None for s in child_shapes):
        return None
    first = child_shapes[0]
    for s in child_shapes[1:]:
        if s != first:
            return None  # non-homogenous
    return (len(obj),) + first  # type: ignore


def add_json_serializable_dict_to_nx_group(
    group: nexus.NXgroup, dictionary: JsonSerializableDict
) -> None:
    """Take a json deserialized dictionary and produces a nexus group for it."""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            sub_group = nexus.NXgroup(nxclass="NXcollection")
            add_json_serializable_dict_to_nx_group(sub_group, value)
            group[key] = sub_group
        elif isinstance(value, str) or _nested_shape(value) is None:
            # String values have to be converted to numpy arrays of string.

            # Numpy can't handle non-homogenous shapes for arrays,
            # which means nexus can't either. If we come accross one then we just
            # convert to string.
            group[key] = nexus.NXfield(value=str(value))
        else:  # This data is can be transformed into a numpy array.
            group[key] = nexus.NXfield(value=value)


def _dict_recursive_get(dictionary: dict, *keys: str) -> Any:
    """Recursively get from a dictionary, e.g
    ``_dict_recursive_get(dictionary, "some", "key", "here")``
    is equivalent to
    ``dictionary.get("some", {}).get("key", {}).get("here", None)``"""
    key, *remaining_keys = keys
    value = dictionary.get(key)
    if isinstance(value, dict) and remaining_keys:
        return _dict_recursive_get(value, *remaining_keys)
    return value


def _leaf_value(attribute_or_field: NxBaseLeaf, object_data: ObjectData) -> nexus.NXfield:
    """Get the value of the leaf data from the bluesky event data, the hints field
    of the stream, or the constant on the ``NxBaseLeaf``, return it as an ``nexus.NXfield``."""

    # If it's an NXfield then add it's attributes.
    attrs = (
        {k: _leaf_value(v, object_data) for k, v in attribute_or_field.nx_attributes().items()}
        if isinstance(attribute_or_field, NxField)
        else {}
    )

    if attribute_or_field.hints_key and object_data.hint:
        return nexus.NXfield(
            value=_dict_recursive_get(cast(dict, object_data.hint), *attribute_or_field.hints_key),
            attrs=attrs,
        )
    if attribute_or_field.data_key and (
        data_key := object_data.formatted_data_key_name_to_data.get(attribute_or_field.data_key)
    ):
        return nexus.NXfield(value=data_key.data, attrs=attrs)
    return attribute_or_field.constant


class _NewFieldType(Enum):
    """Options for how _new_nx_field_from_data_key_data
    should construct it's field."""

    NX_LOG_WITH_TIMESTAMPS = "NX_LOG_WITH_TIMESTAMPS"
    VALUE_ONLY = "VALUE_ONLY"
    TIMESTAMPS_ONLY = "TIMESTAMPS_ONLY"
    NX_DATA_WITH_TIMESTAMPS = "NX_DATA_WITH_TIMESTAMPS"


def _new_nx_field_from_data_key_data(
    nx_field_schema: NxField,
    data_key_data: DataKeyData,
    object_data: ObjectData,
    field_type: _NewFieldType,
    run_start_time: float,
    name: str = "unknown",
) -> nexus.NXlog | nexus.NXfield | nexus.NXdata:
    """Method for getting a new NeXus field.

    ``name`` is not required in the case where the field is directly add to a parent:
    e.g ``group["field_name"] = _new_nx_field_from_data_key_data(...)``.
    """

    attrs = {}
    # Add the specified attributes of the field.
    for nx_attribute_name, nx_attribute in nx_field_schema.nx_attributes().items():
        if nx_attribute_name == "nxclass":
            continue  # This isn't added to fields.
        attribute_value = _leaf_value(nx_attribute, object_data)
        attrs[nx_attribute_name.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)] = nexus.NXfield(
            value=attribute_value
        )

    timestamps_field = nexus.NXfield(
        value=np.array(data_key_data.timestamps) - run_start_time,
        name="timestamps",
        attrs={"units": nexus.NXfield(value="s")},
    )

    if field_type is _NewFieldType.TIMESTAMPS_ONLY:
        timestamps_field.attrs.update(attrs)
        return timestamps_field

    # Add the units from bluesky if not specified in the schema.
    if "units" not in attrs and data_key_data.units:
        attrs["units"] = data_key_data.units

    # NXlog and NXdata are numerical so if the value is a string we give it
    # without timestamps.
    if field_type is _NewFieldType.VALUE_ONLY:
        return nexus.NXfield(value=data_key_data.data, name=name, attrs=attrs)

    # It needs a name "value" for NXlog and NXdata.
    data_field = nexus.NXfield(value=data_key_data.data, name="value", attrs=attrs)

    if field_type is _NewFieldType.NX_LOG_WITH_TIMESTAMPS:
        new_group = nexus.NXlog()
        new_group["time"] = timestamps_field
        new_group["value"] = nexus.NXfield(value=data_key_data.data, name="value", attrs=attrs)
    else:
        new_group = nexus.NXdata(signal=data_field, axes=(timestamps_field,))

    return new_group


def _new_nx_group(
    object_name: str,
    object_data: ObjectData,
    group_schema: NxGroup,
    run_start_time: float,
) -> nexus.NXgroup:
    """Writes the bluesky object into a NeXus group and returns it."""
    # Use the nexusformat class directly if it exists.
    group_initializer = getattr(nexus, group_schema.nxclass.constant, nexus.NXgroup)

    group = group_initializer()
    # nexusformat is wieeerd. If you explicitely make an `nexus.NXsomedevice`
    # then it doesn't seem to make the attribute correctly. This borderline seems
    # like a bug.
    group.attrs["nxclass"] = nexus.NXfield(group_schema.nxclass.constant)

    # Add the specified attributes of the group.
    for nx_attribute_name, nx_attribute in group_schema.nx_attributes().items():
        group.attrs[nx_attribute_name.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)] = _leaf_value(
            nx_attribute, object_data
        )

    for nx_alias, nx_field_schema in group_schema.nx_fields().items():
        if nx_field_schema.hints_key is not None or nx_field_schema.constant is not None:
            group[nx_alias or sanitize_datakey_for_nexus(object_name)] = _leaf_value(
                nx_field_schema, object_data
            )
            continue  # Datakey is from hints/constant.

        if nx_field_schema.timestamps_of_data_key is not None:
            # The schema specifies that this nexus field should come
            # from a data keys timestamps.
            write_value_option = _NewFieldType.TIMESTAMPS_ONLY
            data_key_name = nx_field_schema.timestamps_of_data_key
        else:
            write_value_option = _NewFieldType.NX_LOG_WITH_TIMESTAMPS
            data_key_name = cast(str, nx_field_schema.data_key)

        if data_key_name not in object_data.formatted_data_key_name_to_data:
            # Datakey in schema did not come in this stream.
            continue

        data_key_data = object_data.formatted_data_key_name_to_data[data_key_name]

        if (
            write_value_option is not _NewFieldType.TIMESTAMPS_ONLY
            and isinstance(group_schema, NxData)
            and nx_alias in group_schema.axes.constant + [group_schema.signal.constant]
        ):
            # Contrary to what the documentation would imply, both nexpy,
            # and silx dont accept only nxlog "value" when it counts,
            # e.g plotting an NXdata.
            # TODO: More consideration is needed here. This is a cheap exception,
            # and we won't be able to import nexusformat's NXDATA implementation if this
            # is generatlized.
            write_value_option = _NewFieldType.VALUE_ONLY

        if data_key_data.dtype == "string":
            # NxLog is only applicable for numerical datatypes.
            # TODO: Think about this more.
            write_value_option = _NewFieldType.VALUE_ONLY

        group[nx_alias or sanitize_datakey_for_nexus(object_name)] = (
            _new_nx_field_from_data_key_data(
                nx_field_schema, data_key_data, object_data, write_value_option, run_start_time
            )
        )

    for (
        sub_group_name,
        sub_group_schema,
    ) in group_schema.sub_nx_groups().items():
        group[sub_group_name] = _new_nx_group(
            object_name, object_data, sub_group_schema, run_start_time
        )

    return group


def add_stream_data_to_group(
    stream_group: nexus.NXgroup, stream_data: StreamData, run_start_time: float
) -> None:
    """Take a given stream's parsed `StreamData` and write it to the nexus group."""
    stream_group.attrs["description"] = " A group of devices all read together."

    # Add stream info, e.g descriptor.
    stream_info_group = nexus.NXgroup(nxclass="NXcollection")
    stream_group["stream_info"] = stream_info_group
    descriptor_group = nexus.NXgroup(nxclass="NXcollection")
    stream_info_group["descriptor"] = descriptor_group
    add_json_serializable_dict_to_nx_group(
        descriptor_group, cast(JsonSerializableDict, stream_data.descriptor)
    )

    # Add stream times, e.g event timestamps.
    stream_info_group["time"] = nexus.NXdata(
        signal=nexus.NXfield(
            value=np.array(stream_data.times),
            name="time",
            attrs={"units": nexus.NXfield(value="S")},
        ),
        axes=(
            nexus.NXfield(
                value=stream_data.sequence_numbers,
                name="sequence_number",
                dtype=np.int64,
                # Units purposefully ommited. There isn't really a nice way to quickly
                # summarize this.
            ),
        ),
    )

    # Add devices group to the stream.
    devices_group = nexus.NXgroup(nxclass="NXinstrument")
    stream_group["devices"] = devices_group

    for object_name, object_data in stream_data.object_data.items():
        if isinstance(object_data.nx_schema, NxGroup):
            device_group = _new_nx_group(
                object_name, object_data, object_data.nx_schema, run_start_time
            )

            for (
                nx_attribute_name,
                nx_attribute,
            ) in object_data.nx_schema.nx_attributes().items():
                device_group.attrs[
                    nx_attribute_name.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)
                ] = _leaf_value(nx_attribute, object_data)

            # TODO: It would be lovely to use `nexusformat.nexus.validate.GroupValidator` here,
            # e.g  `group_validator = GroupValidator(object_data.nx_schema.nxclass.constant)`
            # then validate the group, if it fails, then warn and make a default group.
            # There would need to be changes in nexusformat for this. Mainly, there's no API
            # for receiving the errors other than just logging them, but also, taking the
            # taking the example from
            # `test_passing_bluesky_nexus.base_schema_but_incorrect_nexusformat_definitions`,
            # we get things like:
            # 2026-08-14 11:19:29 [CRITICAL] NXValidate: NXdata: data
            # "@signal" is not present in the group
            # but signal is an optional argument in the schema.
            # Futhermore, there isn't an exact correspondance between the NXDL and
            # what we'd want in a basemodel. Some fields are defined with assumed
            # logic on the writer side.
            devices_group[sanitize_datakey_for_nexus(object_name)] = device_group

        elif isinstance(object_data.nx_schema, NxField):
            # It has a single nx_field, no group...
            if object_data.nx_schema.data_key not in object_data.formatted_data_key_name_to_data:
                LOGGER.warning(
                    f"Datakey `{object_data.nx_schema.data_key}` in schema not "
                    "accounted for in an event stream captured... Skipping it."
                )
                continue
            devices_group[sanitize_datakey_for_nexus(object_name)] = (
                _new_nx_field_from_data_key_data(
                    object_data.nx_schema,
                    object_data.formatted_data_key_name_to_data[object_data.nx_schema.data_key],
                    object_data,
                    _NewFieldType.NX_DATA_WITH_TIMESTAMPS,
                    run_start_time,
                    name=object_name,
                )
            )


def create_nexus_structure(run_data: RunData) -> nexus.NXroot:
    """Create a nexus structure (`NXroot`) from the data
    in a bluesky plan."""
    start_time = time.perf_counter()
    root = nexus.NXroot()
    entry = nexus.NXentry()
    add_json_serializable_dict_to_nx_group(
        entry,
        {
            "Application name": "bluesky_nexus",
            "Application version": __version__,
            "Content": "A bluesky run's documents parsed to nexus.",
        },
    )

    root["entry"] = entry

    # Add the run start and run stop.
    run_info = nexus.NXgroup(name="run_info", nxclass="NXcollection")
    run_start_group = nexus.NXgroup(name="run_start", nxclass="NXcollection")
    add_json_serializable_dict_to_nx_group(
        run_start_group, cast(JsonSerializableDict, run_data.run_start)
    )
    run_info["run_start"] = run_start_group
    run_stop_group = nexus.NXgroup(name="run_stop", nxclass="NXcollection")
    add_json_serializable_dict_to_nx_group(
        run_stop_group, cast(JsonSerializableDict, run_data.run_stop)
    )
    run_info["run_stop"] = run_stop_group
    entry["run_info"] = run_info

    # Add each stream.
    for stream_name, stream_data in run_data.stream_name_to_stream_data.items():
        if stream_name in entry:
            LOGGER.warning(
                f"Cannot add stream {stream_name} as there is already a field named that "
                "in the bluesky nexus structure."
            )
            continue
        try:
            new_stream_group = nexus.NXgroup(nxclass="NXcollection")
            add_stream_data_to_group(new_stream_group, stream_data, run_data.run_start["time"])
        except Exception as _:
            LOGGER.warning(
                f"Failed to write stream {stream_name}, will try with the others...",
                exc_info=True,
            )
        else:
            entry[stream_name] = new_stream_group

    LOGGER.info(f"Parsed nexus structure from run in {time.perf_counter() - start_time}s.")
    return root
