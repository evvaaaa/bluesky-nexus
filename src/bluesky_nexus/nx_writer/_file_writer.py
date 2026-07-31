from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, TypeAlias, Union, cast

import numpy as np
from nexusformat import nexus

from bluesky_nexus import __version__, schema
from bluesky_nexus.common.logging_utils import log_time_taken, logger
from bluesky_nexus.nx_writer._data_extractor import DataKeyData, ObjectData, StreamData
from bluesky_nexus.schema.nx_group import NxGroup

from ._data_extractor import RunData

JsonSerializableScalar: TypeAlias = str | int | str | bool | float | None
# typing.Union required for future recursive references... annoooooying
JsonSerializableList: TypeAlias = list[
    Union[JsonSerializableScalar, "JsonSerializableList"]
]
JsonSerializableTuple: TypeAlias = list[
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


def dump_json_serializable_dict_to_nx_group(
    group: nexus.NXgroup, dictionary: JsonSerializableDict
) -> None:
    """Take a json deserialized dictionary and produces a nexus group for it."""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            sub_group = nexus.NXgroup(name=key, nxclass="NXcollection")
            dump_json_serializable_dict_to_nx_group(sub_group, value)
            group[key] = sub_group
        elif isinstance(value, str) or not _is_homogeneous_iterable_or_scalar(value):
            # String values have to be converted to numpy arrays of string.

            # Numpy can't handle non homogenous shapes for arrays,
            # which means nexus can't either. If we come accross one then we just
            # convert to string.
            group[key] = nexus.NXfield(value=str(value), name=key)
        else:
            group[key] = nexus.NXfield(value=value, name=key)


def _new_nx_field(
    nx_field_schema: schema.NxField, data_key_data: DataKeyData
) -> nexus.NXfield:
    new_field = nexus.NXfield(value=data_key_data.data)
    if nx_field_schema.nx_units:
        new_field["units"] = nexus.NXfield(value=nx_field_schema.nx_units)
    return new_field


def _write_nx_object(
    group: nexus.NXgroup, object_data: ObjectData, group_schema: NxGroup
) -> None:
    """Write the object into a nexus group."""
    group.attrs["nxclass"] = group_schema.nx_class
    for nx_field_schema in group_schema.nx_fields().values():
        data_key_data = object_data.data_key_data[nx_field_schema.datakey]
        group[nx_field_schema.nx_alias] = _new_nx_field(nx_field_schema, data_key_data)

    for (
        sub_group_name,
        sub_group_schema,
    ) in group_schema.sub_nx_groups().items():
        sub_group = nexus.NXgroup()
        _write_nx_object(sub_group, object_data, group_schema=sub_group_schema)
        group[sub_group_name] = sub_group


def write_stream(
    run_start_time: float, stream_group: nexus.NXgroup, stream_data: StreamData
) -> None:
    """Take a given stream's parsed `StreamData` and write it to the nexus group."""
    dump_json_serializable_dict_to_nx_group(
        stream_group, {"description": "A collection of devices all read together."}
    )

    stream_group["read_times"] = nexus.NXdata(
        signal=nexus.NXfield(
            value=np.array(stream_data.read_times) - run_start_time,
            name="time",
            attrs={"units": nexus.NXfield(value="S")},
        ),
        axes=(
            nexus.NXfield(
                value=stream_data.sequence_numbers,
                name="sequence_number",
                dtype=np.int64,
                attrs={"units": nexus.NXfield(value="seq num")},
                # Units purposefully ommited. There isn't really a nice way to quickly
                # summarize this.
            ),
        ),
    )
    for object_name, object_data in stream_data.object_data.items():
        object_group = nexus.NXgroup()
        _write_nx_object(object_group, object_data, object_data.nx_schema)
        stream_group[object_name] = object_group


class NexusFileWriter:
    def __init__(self, path: Path):
        self._path = path

    @log_time_taken
    def create_file(self, run_data: RunData):
        root = nexus.NXroot()
        entry = nexus.NXentry()
        dump_json_serializable_dict_to_nx_group(
            entry,
            {
                "Application name": "bluesky_nexus",
                "Application version": __version__,
                "Content": "'NXinstrument' group and 'NXcollection' group",
            },
        )

        root["entry"] = entry

        # Add the run start and run stop.
        run_info = nexus.NXgroup(name="run_info", nxclass="NXcollection")
        run_start_group = nexus.NXgroup(name="run_start", nxclass="NXcollection")
        dump_json_serializable_dict_to_nx_group(
            run_start_group, cast(JsonSerializableDict, run_data.run_start)
        )
        run_info["run_start"] = run_start_group
        run_stop_group = nexus.NXgroup(name="run_stop", nxclass="NXcollection")
        dump_json_serializable_dict_to_nx_group(
            run_stop_group, cast(JsonSerializableDict, run_data.run_stop)
        )
        run_info["run_stop"] = run_stop_group
        entry["run_info"] = run_info

        for stream_name, stream_data in run_data.stream_name_to_stream_data.items():
            # Add each stream
            try:
                new_stream_group = nexus.NXgroup(name=stream_name)
                write_stream(run_data.start_time, new_stream_group, stream_data)
            except Exception as _:
                logger.warning(
                    f"Failed to write stream {stream_name}, "
                    "will try with the others...",
                    exc_info=True,
                )
            else:
                entry[stream_name] = new_stream_group

        try:
            root.save(self._path, mode="w")
        except Exception as _:
            logger.warning(f"Failed to write file {self._path}...", exc_info=True)
        else:
            logger.info("NeXus file '%s' created successfully.", self._path)
