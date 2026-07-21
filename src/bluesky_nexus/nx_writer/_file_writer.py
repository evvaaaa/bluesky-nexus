from pathlib import Path

import h5py
import numpy as np

from bluesky_nexus.common.logging_utils import logger

from ._document_parser import ParsedDevice


class NexusFileWriter:
    def __init__(
        self,
        path: Path,
    ):
        self._path = path

    def create_file(self, run_info: dict):
        with h5py.File(self._path, "w") as f:
            # Create file level attribute
            f.attrs["default"] = "entry"

            # Create the NXentry group
            entry = f.create_group("entry")
            entry.attrs["NX_class"] = "NXentry"
            entry.attrs["Application name"] = "bluesky_nexus"
            entry.attrs["Content"] = "'NXinstrument' group and 'NXcollection' group"

            run_info_group = entry.create_group("run_info")
            run_info_group.attrs["NX_class"] = "NXcollection"
            run_info_group.attrs["description"] = (
                "Copy of the start and stop document from the bluesky run."
            )
            # Write data to the run_info_group
            write_collection(run_info_group, run_info)

            logger.info("NeXus file '%s' created successfully.", self._path)

    def write_stream(self, stream_name: str, devices: list[ParsedDevice]):
        with h5py.File(self._path, "w") as f:
            stream_group = f.create_group(stream_name)
            stream_group.attrs["description"] = (
                "A collection of devices all read together."
            )
            for device in devices:
                device_group = stream_group.create_group(device._object_key)
                device_group.attrs["NX_class"] = device.nx_class

                device.write_into_group(stream_group)


def write_collection(group, data: dict) -> None:
    """Write collection.

    Recursively writes a collection of data (nested dictionaries, lists, and
    primitive values) to a given group in a hierarchical storage structure.
    Scalars are stored as 1D arrays.

    Args:
        group (h5py.Group): The group where the data will be stored.
        data (dict): The data dictionary to be written.

    Raises:
        TypeError: If an unsupported data type is encountered.
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
