from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeAlias, Union, cast

import numpy as np
from nexusformat import nexus

from bluesky_nexus import __version__, nx_schema
from bluesky_nexus.common.logging_utils import log_time_taken, logger
from bluesky_nexus.nx_schema.nx_base import NxField, NxGroup

from ._data_extractor import (
    DataKeyData,
    ObjectData,
    RunData,
    StreamData,
)

JsonSerializableScalar: TypeAlias = str | int | bool | float | None
# typing.Union required for future recursive references... annoooooying
JsonSerializableList: TypeAlias = list[
    Union[JsonSerializableScalar, "JsonSerializableList"]
]
JsonSerializableTuple: TypeAlias = tuple[
    Union[JsonSerializableScalar, "JsonSerializableTuple"]
]
JsonSerializableDict: TypeAlias = dict[
    str,
    Union[
        JsonSerializableScalar,
        JsonSerializableList,
        JsonSerializableTuple,
        "JsonSerializableDict",
    ],
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


def _is_homogeneous_iterable_or_scalar(obj: Any) -> bool:
    return _nested_shape(obj) is not None


def add_json_serializable_dict_to_nx_group(
    group: nexus.NXgroup, dictionary: JsonSerializableDict
) -> None:
    """Take a json deserialized dictionary and produces a nexus group for it."""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            sub_group = nexus.NXgroup(nxclass="NXcollection")
            add_json_serializable_dict_to_nx_group(sub_group, value)
            group[key] = sub_group
        elif isinstance(value, str) or not _is_homogeneous_iterable_or_scalar(value):
            # String values have to be converted to numpy arrays of string.

            # Numpy can't handle non homogenous shapes for arrays,
            # which means nexus can't either. If we come accross one then we just
            # convert to string.
            group[key] = nexus.NXfield(value=str(value))
        else:
            group[key] = nexus.NXfield(value=value)


def _new_nx_field(
    nx_field_schema: nx_schema.NxField,
    data_key_data: DataKeyData,
    name: str = "unknown",
) -> nexus.NXfield:
    """Util method for adding new nx field. name is not required
    if the field is directly added to a parent,
    e.g group["field_name"] =...
    """
    attrs = {}
    if nx_field_schema.nx_units:
        attrs["units"] = nexus.NXfield(value=nx_field_schema.nx_units)
    return nexus.NXfield(value=data_key_data.data, name=name, attrs=attrs)


def _add_nx_object_data_to_group(
    object_name: str,
    group: nexus.NXgroup,
    object_data: ObjectData,
    group_schema: nx_schema.NxGroup,
) -> None:
    """Write the object into a nexus group."""
    group.attrs["nxclass"] = group_schema.nx_class

    for nx_field_schema in group_schema.nx_fields().values():
        if nx_field_schema.datakey not in object_data.formatted_data_key_name_to_data:
            continue
        data_key_data = object_data.formatted_data_key_name_to_data[
            nx_field_schema.datakey
        ]
        group[nx_field_schema.nx_alias or object_name] = _new_nx_field(
            nx_field_schema, data_key_data
        )

    for (
        sub_group_name,
        sub_group_schema,
    ) in group_schema.sub_nx_groups().items():
        sub_group = nexus.NXgroup()
        _add_nx_object_data_to_group(
            object_name, sub_group, object_data, group_schema=sub_group_schema
        )
        group[sub_group_name] = sub_group


def add_stream_data_to_group(
    run_start_time: float, stream_group: nexus.NXgroup, stream_data: StreamData
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
    # Add new timestamps group
    timestamps_group = nexus.NXgroup(nxclass="NXsubentry")
    stream_info_group["timestamps"] = timestamps_group
    timestamps_group.attrs["description"] = (
        "The timestamps of the reads of each individual read on the device signal, "
        "instead of the read of the stream through bluesky."
    )
    for object_data in stream_data.object_data.values():
        for (
            data_key,
            data_key_data,
        ) in object_data.data_key_name_to_data.items():
            timestamps_group[data_key] = nexus.NXfield(value=data_key_data.timestamps)

    # Add devices
    devices_group = nexus.NXgroup(nxclass="NXinstrument")
    stream_group["devices"] = devices_group
    devices_group["time"] = nexus.NXdata(
        signal=nexus.NXfield(
            value=np.array(stream_data.times) - run_start_time,
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

    for object_name, object_data in stream_data.object_data.items():
        if isinstance(object_data.nx_schema, NxGroup):
            device_group = nexus.NXgroup()
            _add_nx_object_data_to_group(
                object_name, device_group, object_data, object_data.nx_schema
            )
            devices_group[object_name] = device_group
        elif isinstance(object_data.nx_schema, NxField):
            # It has a single nx_field, no group...
            if (
                object_data.nx_schema.datakey
                not in object_data.formatted_data_key_name_to_data
            ):
                logger.warning(
                    f"Datakey `{object_data.nx_schema.datakey}` in schema not accounted"
                    " for in an event stream captured... Skipping it."
                )
                continue
            devices_group[object_name] = _new_nx_field(
                object_data.nx_schema,
                object_data.formatted_data_key_name_to_data[
                    object_data.nx_schema.datakey
                ],
                object_name,
            )


@log_time_taken
def create_nexus_structure(run_data: RunData) -> nexus.NXroot:
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
        try:
            new_stream_group = nexus.NXgroup(nxclass="NXsubentry")
            add_stream_data_to_group(run_data.start_time, new_stream_group, stream_data)
        except Exception as _:
            logger.warning(
                f"Failed to write stream {stream_name}, will try with the others...",
                exc_info=True,
            )
        else:
            entry[stream_name] = new_stream_group

    return root
