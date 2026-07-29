from pathlib import Path
from typing import Any

import h5py
import numpy as np
from numpy.typing import DTypeLike

from bluesky_nexus import __version__
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.schema._base_schema import NxBase

from ._data_extractor import ObjectData, RunData, StreamData


class NexusFileWriter:
    def __init__(self, path: Path):
        self._path = path

    def create_file(self, run_data: RunData):
        with h5py.File(self._path, "w") as f:
            # Create file level attribute
            f.attrs["default"] = "bluesky run"

            # Create the NXentry group
            # TODO: Call it something more relevant to the run
            entry = f.create_group("bluesky plan")
            entry.attrs["NX_class"] = "NXentry"
            entry.attrs["Application name"] = "bluesky_nexus"
            entry.attrs["Application version"] = __version__
            entry.attrs["Content"] = "'NXinstrument' group and 'NXcollection' group"

            run_info_group = entry.create_group("run_info")
            run_info_group.attrs["NX_class"] = "NXcollection"
            run_info_group.attrs["description"] = (
                "Copy of the start and stop document from the bluesky run."
            )
            # Write data to the run_info_group
            write_collection(
                run_info_group, {"start": run_data.run_start, "stop": run_data.run_stop}
            )

            for stream_name, stream_data in run_data.stream_name_to_stream_data.items():
                stream_group = f.create_group(stream_name)
                self.write_stream(stream_group, stream_data)
            logger.info("NeXus file '%s' created successfully.", self._path)

    def write_object(
        self,
        object_group: h5py.Group,
        object_data: ObjectData,
        current_level_in_schema: NxBase | None = None,
    ):
        current_level_in_schema = current_level_in_schema or object_data.nx_schema
        for _nx_field in current_level_in_schema.nx_fields():
            object_data.data_key_data.get()

    def write_stream(self, stream_group: h5py.Group, stream_data: StreamData):
        stream_group.attrs["description"] = "A collection of devices all read together."

        write_dataset(
            stream_group,
            "sequence_numbers",
            stream_data.sequence_numbers,
            np.int64,
            units="Seq Num",
        )

        write_dataset(
            stream_group,
            "read_times",
            stream_data.read_times,
            np.float64,
            units="S (epoch)",
        )

        for object_name, object_data in stream_data.object_data.items():
            object_group = stream_group.create_group(object_name)
            self.write_object(object_group, object_data)


def write_dataset(
    parent: h5py.Group,
    name: str,
    data: list[Any],
    dtype: DTypeLike,
    units: str | None = None,
    description: str | None = None,
):
    new_dataset = parent.create_dataset(name, data=np.array(data, dtype=dtype))
    if units is not None:
        new_dataset.attrs["units"] = units
    if description is not None:
        new_dataset.attrs["Description"] = description


def write_collection(group: h5py.Group, data: dict) -> None:
    """
    Recursively writes a collection of data (nested dictionaries, lists, and
    primitive values) to a given group in a hierarchical storage structure.
    Scalars are stored as 1D arrays.
    """
    string_dtype = h5py.string_dtype(encoding="utf-8")

    for key, value in data.items():
        if isinstance(value, dict):
            # Create a subgroup for nested data dictionaries
            subgroup = group.create_group(key)
            write_collection(subgroup, value)

        elif isinstance(value, (int, float, bool)):
            # Store scalar as 1D array
            group.create_dataset(key, data=np.array([value]))

        elif isinstance(value, str):
            # Store string as 1D array with UTF-8 dtype
            group.create_dataset(key, data=np.array([value], dtype=string_dtype))

        elif isinstance(value, (list, tuple)):
            # List or tuple with nested list or tuple elements
            if any(isinstance(item, (list, tuple)) for item in value):
                # Serialize nested structure into a single string
                serialized_value = str(value)
                group.create_dataset(
                    key, data=np.array([serialized_value], dtype=string_dtype)
                )
            # List or tuple without nested list or tuple elements
            else:
                if len(value) == 0:
                    # Empty list or tuple
                    group.create_dataset(key, data=np.array([], dtype=string_dtype))
                elif all(isinstance(item, (int, float, bool)) for item in value):
                    group.create_dataset(key, data=np.array(value))
                else:
                    # Convert mixed-type or string-containing list to strings
                    str_value = [str(item) for item in value]
                    group.create_dataset(
                        key, data=np.array(str_value, dtype=string_dtype)
                    )

        else:
            logger.error("Unsupported type '%s' for key '%s'", type(value), key)
            raise TypeError(f"ERROR: Unsupported type {type(value)} for key '{key}'")
