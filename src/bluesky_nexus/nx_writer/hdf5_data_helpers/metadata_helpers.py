"""metadata_helpers.py.

Utility functions for processing and enriching Nexus metadata with Bluesky event and
descriptor data.

This module provides helper functions used to manipulate and resolve metadata fields
during post-processing of experimental data. These utilities are primarily used in
workflows where Bluesky event streams are mapped to Nexus-compatible formats, especially
for resolving data types and filling in optional metadata attributes.

Functions:
    - resolve_dtype: Determines the appropriate dtype for a given metadata field.
    - assign_optional_attrs: Enriches an object's attribute dictionary with optional
    metadata fields such as units, precision, and control limits.

These utilities are typically used internally by higher-level functions that transform
`$post-run` placeholders in metadata templates into concrete values derived from
experimental runs.
"""


def resolve_dtype(obj_dtype, desc, obj_attrs):
    """Resolve the appropriate data type (dtype) for an object.

    based on input parameters.

    Parameters:
        obj_dtype (str or None): An explicitly provided data type. If not None, this is
        prioritized.
        desc (dict): A description dictionary that may contain a "dtype" key indicating
        the intended type.
        obj_attrs (dict): A dictionary of object attributes, used especially for arrays
        to determine the dtype.

    Returns:
        str: The resolved data type as a string. Possible return values include:
            - "float64" for numeric types or arrays with no specified dtype.
            - "int64" for integers.
            - "str" for strings and generic objects.
            - A custom or passed-through dtype if not matched by standard types.
    """
    dtype = obj_dtype or desc.get("dtype", "unknown")
    if dtype == "number":
        return "float64"
    if dtype == "integer":
        return "int64"
    if dtype == "string":
        return "str"
    if dtype == "array":
        return obj_attrs.get("dtype", "float64")
    if dtype == "object":
        return "str"
    return dtype


def assign_optional_attrs(obj_attrs, desc):
    """Assign optional attributes to an object's attribute dictionary.

    based on available values.

    This function checks for a predefined set of optional keys and assigns values
    to `obj_attrs`
    from either `obj_attrs` itself or, if not present, from the `desc` dictionary.
    Attributes are only set if a non-None value is found.

    Parameters:
        obj_attrs (dict): The dictionary of object attributes to be updated.
        desc (dict): A description dictionary that may provide default values for
        optional attributes.

    Modifies:
        obj_attrs (dict): Updates in-place with optional keys if values are found in
        either source.
    """
    optional_keys = [
        "units",
        "external",
        "precision",
        "lower_ctrl_limit",
        "upper_ctrl_limit",
        "enum_strs",
        "object_name",
    ]
    for key in optional_keys:
        val = obj_attrs.get(key, desc.get(key, None))
        if val is not None:
            obj_attrs[key] = val
