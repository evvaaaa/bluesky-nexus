"""placeholder_helpers.py.

Utilities for resolving and replacing `$post-run` placeholders in Nexus metadata.

This module provides tools to traverse a nested metadata structure (tree), detect
special placeholder strings (e.g., `$post-run:<component>`), and replace them with
actual measurement data extracted from Bluesky descriptors and event documents.

Key Features:
------------
- Supports parsing and validating post-run placeholders.
- Extracts component data and timestamps using helper functions from `data_extraction`.
- Applies symbolic transformations to extracted data if specified.
- Dynamically infers data type (`dtype`), shape, and optional metadata attributes.
- Recursively replaces placeholders in nested structures (lists or dicts).

Typical Use Case:
-----------------
Used as part of a metadata post-processing step to enrich Nexus metadata structures
with actual run data after a Bluesky experiment has completed. This ensures the
metadata tree reflects the true recorded values for relevant hardware components.

Key Functions:
--------------
- `get_cpt_name_from_placeholder`: Extracts the component name from a `$post-run`
    string.
- `replace_func`: Replaces a single `$post-run` value with real data from a run.
- `replace_values`: Recursively applies `replace_func` to a nested metadata tree.

Dependencies:
-------------
- `bluesky_nexus.callbacks.nexus_writer.data_extraction_helpers ` for retrieving data
    from descriptors and events.
- `bluesky_nexus.callbacks.nexus_writer.metadata_helpers` for dtype resolution and
    attribute assignment.
- `bluesky_nexus.callbacks.nexus_writer.symbolic_transformation_helpers` for
    transforming numeric data using expressions.
"""

import re
from typing import Callable, Deque, Optional, Union

import numpy as np

from bluesky_nexus.callbacks.nexus_writer.data_extraction_helpers import extract_data
from bluesky_nexus.callbacks.nexus_writer.metadata_helpers import (
    assign_optional_attrs,
    resolve_dtype,
)
from bluesky_nexus.callbacks.nexus_writer.symbolic_transformation_helpers import (
    apply_symbolic_transformation,
)


# Define a few helper functions to parse the Nexus tree
# and replace values with data from the events of the run
def get_cpt_name_from_placeholder(value: str) -> Optional[str]:
    """get_cpt_name_from_placeholder.

    Extracts the component name from the placeholder string,
    typically in the form of `$post-run:<component_name>`.

    Args:
        value (str): The placeholder string, e.g., "$post-run:a_b_c".
        Pattern matches:
            $post-run:a_b_c
            $post-run:a-b-c-d
            $post-run:a_b-c_d-e
            $post-run:a
            $post-run

    Returns:
        str: The component name extracted from the placeholder
        (e.g., "a_b_c").
        None: If the placeholder does not match the expected pattern.
    """
    post_run_label: str = "$post-run:"
    pattern: str = r"^\$post-run(:[a-zA-Z0-9_-]+)?$"

    match = re.search(pattern, value)
    if match:
        if len(post_run_label) < len(value):
            cpt_name: str = value[len(post_run_label) :]
            return cpt_name
        return str("")  # Return empty string
    return None  # Pattern does not match


def replace_func(
    dev_name: str,
    obj: dict,
    descriptors: Deque,
    events: Deque,
    delimiter: str = "_",
) -> dict:
    """Replace a `$post-run` placeholder.

    Replace a `$post-run` placeholder in a metadata object with actual
    event-derived data.

    This function checks whether the 'value' field in `obj` is a `$post-run`
    placeholder.
    If so, it:
        - Parses the placeholder to determine the component name.
        - Extracts corresponding data from event or descriptor documents.
        - Resolves data type and attributes.
        - Applies any requested transformation to the value.
        - Replaces the original placeholder with the real data and metadata.

    Args:
        dev_name (str): Name of the device from the Nexus metadata tree.
        obj (dict): Dictionary representing a single data field, possibly with
        a `$post-run` value.
        descriptors (Deque): Collection of descriptor documents from the run.
        events (Deque): Collection of event documents from the run.
        delimiter (str): Delimiter used to join `dev_name` and `cpt_name` in Bluesky
        (typically '_').

    Returns:
        dict: A copy of `obj`, possibly with updated `value`, `dtype`, `shape`,
        timestamps, and attributes.
    """
    if "value" not in obj:
        return obj

    placeholder: str = obj["value"]
    if not isinstance(placeholder, str):
        return obj

    # Define component name
    cpt_name: Optional[str] = get_cpt_name_from_placeholder(placeholder)
    if cpt_name is None:
        return obj

    # Redefine component name as to be read from
    # the bluesky documents (with prefixed device name)
    if "" == cpt_name:  # The case when there is not cpt_name in the placeholder
        cpt_name = dev_name
    else:
        cpt_name = f"{dev_name}{delimiter}{cpt_name}"

    # Extract data from descriptor for the component
    cpt_data: Optional[dict] = extract_data(descriptors, events, cpt_name)

    # Return obj if no data for the component with
    # cpt_name could be extracted from descriptors
    if not cpt_data:
        return obj

    # Component data from descriptor
    data: np.ndarray = cpt_data["data"]
    # Component description from descriptor
    desc: dict = cpt_data["description"]

    # Optional transformation on data of data
    if "transformation" in obj:
        # Execute transformation on events_data
        transformation = obj["transformation"]
        if "value" == transformation.get("target"):
            expression: str = transformation.get("expression", "")
            data = apply_symbolic_transformation(data, expression)

    # Assign 'data'
    obj["value"] = data

    # Assign 3 extra keys if present
    for key in [
        "events_cpt_timestamps",
        "events_timestamps",
        "descriptor_cpt_timestamp",
    ]:
        if key in cpt_data:
            obj[key] = cpt_data[key]

    # ----------- Assign all obligatory keys -----------
    obj_dtype = obj.get("dtype")
    obj_attrs = obj.setdefault("attrs", {})  # Ensure "attrs" key exists in obj
    obj["dtype"] = resolve_dtype(obj_dtype, desc, obj_attrs)

    # Assign shape (obligatory key)
    obj["shape"] = list(data.shape)

    # Extract and set source (obligatory key)
    obj_attrs["source"] = obj_attrs.get("source", desc.get("source", "unknown"))

    # ----------- Assign all optional keys -----------
    assign_optional_attrs(obj_attrs, desc)
    return obj


def replace_values(
    dev_name: str, tree: Union[dict, list], func: Callable[[str, dict], dict]
) -> Union[dict, list]:
    """Recursively replace placeholders in a tree.

    Recursively walk a tree and apply a transformation function to objects with
    a 'value' key.

    Traverses a nested structure (dicts and lists), calling `func(dev_name, obj)`
    on any dict that contains a 'value' field. Used to replace `$post-run`
    placeholders in Nexus metadata.

    Args:
        dev_name (str): Name of the device (used to construct component keys).
        tree (Union[dict, list]): A nested dictionary or list structure to traverse.
        func (Callable[[str, dict], dict]): A function that takes (dev_name, obj)
        and returns a transformed obj.

    Returns:
        Union[dict, list]: The original tree with applicable values replaced
        by the result of `func`.
    """
    if isinstance(tree, dict):
        for key, value in tree.items():
            if isinstance(value, dict) and "value" in value:
                tree[key] = func(dev_name, value)
            tree[key] = replace_values(dev_name, value, func)
    elif isinstance(tree, list):
        tree = [replace_values(dev_name, item, func) for item in tree]
    return tree
