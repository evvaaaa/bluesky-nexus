"""group_helpers.py.

Helpers for creating and managing HDF5 groups and datasets.

This module provides functions to recursively add NeXus-compliant groups and datasets
to an HDF5 file structure within NeXus files using the h5py library.
It supports handling of attributes, special timestamp datasets, and various metadata
conventions defined by the NeXus standard.

Main functionality includes:
- Recursively creating groups and datasets with appropriate NX_class attributes.
- Adding attributes to groups and datasets, supporting both schema-defined and
  user-defined metadata.
- Handling special cases such as timestamp datasets with specific processing.
- Validating dataset dtypes against a known set of valid NeXus field types.

The core function `add_group_or_field` processes nested dictionaries describing
the NeXus file structure, creating groups, datasets, and assigning attributes
accordingly.
"""

from typing import Any, Dict, Union

import h5py  # type: ignore

from bluesky_nexus.bluesky_nexus_const import VALID_NXFIELD_DTYPES
from bluesky_nexus.callbacks.nexus_writer.attributes_helpers import add_attributes
from bluesky_nexus.callbacks.nexus_writer.attrs_helpers import add_attrs
from bluesky_nexus.callbacks.nexus_writer.dataset_helpers import (
    create_dataset_with_value,
)
from bluesky_nexus.callbacks.nexus_writer.timestamp_helpers import (
    add_events_timestamps,
    add_special_timestamps,
)
from bluesky_nexus.common.logging_utils import logger


def add_group_or_field(group: h5py.Group, data: Union[Dict[str, Any], Any]) -> None:
    """Add group or field.

    Recursively adds groups or datasets to a NeXus file based on the provided
    data.

    Parameters:
        group (h5py.Group): The parent group to which fields or subgroups will
            be added.
        data (dict): A dictionary describing the NeXus structure. Keys
        represent names of groups or fields, and values provide detailed
        metadata such as `NX_class`, `value`, `dtype`, and attributes.

    Raises:
        ValueError: If invalid `dtype` is encountered for a dataset.

    Example:
        data = {
            "mono": {
                "NX_class": "NXmonochromator",
                "value": 123.4,
                "dtype": "float64",
                "attrs": {"units": "keV"}
            }
        }
        add_group_or_field(parent_group, data)
    """

    def process_dataset(key: str, value: dict) -> None:

        # dtype assigned in the pydantic schema
        # or extracted from the descriptor doc
        dtype = value.get("dtype", None)

        if dtype not in VALID_NXFIELD_DTYPES:
            raise ValueError(
                f"Invalid dtype: {dtype} for key: {key} in group: {group.name}"
            )

        ds: h5py.Dataset = create_dataset_with_value(key, value["value"], dtype, group)

        # Add attributes to the dataset
        # In the schema file, attributes of a field are introduced
        # by the word "attributes"
        # Each attribute has a value and dtype
        # Attribute of dataset can be: scalar or array
        # Attribute of dataset can be of type: defined under VALID_NXFIELD_DTYPES
        if "attributes" in value:
            add_attributes(ds, value["attributes"])

        # Add attribute 'shape' (obligatory)
        if "shape" in value:
            ds.attrs["shape"] = value["shape"]

        # Add attribute 'NX_class' (obligatory)
        if "nxclass" in value:
            ds.attrs["NX_class"] = value["nxclass"]

        # Add attribute 'transformation' (optional)
        if "transformation" in value:
            # convert dict to string
            ds.attrs["transformation"] = str(value["transformation"])

        # Add all attributes defined in 'attrs'
        if "attrs" in value:
            add_attrs(ds, value["attrs"])

        # Handle special timestamp datasets
        if "events_cpt_timestamps" in value:
            add_special_timestamps(key, "events_cpt_timestamps", value, group)

        if "descriptor_cpt_timestamp" in value:
            add_special_timestamps(key, "descriptor_cpt_timestamp", value, group)
        if "events_timestamps" in value:
            add_events_timestamps(key, value, group)

    def process_group(key: str, value: dict) -> None:

        # Create group
        subgroup = group.create_group(key)

        logger.debug(
            "New subgroup: %s added to the group: %s", subgroup.name, group.name
        )

        # Add "NX_class" attribute expected by nexus convention for groups
        subgroup.attrs["NX_class"] = value["nxclass"]

        # Add "default" attribute expected by nexus convention for groups
        # if defined for the group
        if "default" in value:
            # Presence of “value” in the “default” guaranteed by NXattrModel
            subgroup.attrs["default"] = value["default"]["value"]

        # Add attributes to the group defined in the schema
        # In the schema file, attributes of a group are introduced
        # by the word "attributes"
        # Each attribute has a value and dtype
        # Attribute of a group can be: integer, float, string, bool, array
        # Attribute of a group can be of type: str, int32, int64, float32,
        # float64, bool
        if "attributes" in value:
            add_attributes(subgroup, value["attributes"])

        # Add all attributes defined in 'attrs'
        if "attrs" in value:
            add_attrs(subgroup, value["attrs"])

        # Recursively add fields or subgroups
        nested_data = {
            k: v
            for k, v in value.items()
            if k not in {"nxclass", "default", "attributes", "attrs"}
        }
        add_group_or_field(subgroup, nested_data)

    for key, value in data.items():
        if isinstance(value, dict):

            # Handle dataset (field) with "value"
            # value["value"] is in "post-run" case always numpy array
            if "value" in value:
                process_dataset(key, value)

            # Handle NeXus groups
            elif "nxclass" in value:
                process_group(key, value)

            else:
                logger.warning("Unrecognized dict structure at key: %s", key)
        else:
            # Handle as attribute of the group
            group.attrs[key] = value
            logger.debug(
                "Assign to attrs of group: %s the key: %s with value: %s",
                group.name,
                key,
                value,
            )
