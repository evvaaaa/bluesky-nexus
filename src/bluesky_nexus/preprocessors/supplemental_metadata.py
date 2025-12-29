"""Module supplemental_metadata.

Module for Managing and Injecting Supplemental Metadata in Bluesky Plans

This module provides utilities to manage, validate, and inject supplemental
metadata into Bluesky plans. The primary feature is the SupplementalMetadata
class, which extends the functionality of Bluesky's SupplementalData to
dynamically generate and inject metadata based on device-specific attributes.
It includes support for two types of metadata: device metadata (DEVICE_MD)
and NeXus metadata (NEXUS_MD).

Key Features:

    Dynamically generate metadata for all devices defined in 'devices_dictionary'.
    Support for placeholder resolution in NeXus metadata, handling missing
    data gracefully.
    Utilities for metadata extraction, processing, and validation.

Classes:

    SupplementalMetadata: Extends SupplementalData to manage device metadata
    injection.

Functions:

    create_device_md: Generates a device metadata dictionary using device
    attributes.
    create_nexus_md: Generates NeXus-compliant metadata with placeholder
    resolution.
    create_metadata: A generic function for extracting metadata using a
    provided extraction function.
    process_value_not_available: Removes keys with values marked as
    "NOT_AVAILABLE".
    resolve_pre_run_placeholders: Recursively resolves placeholders in
    metadata dictionaries.
    get_nested_dict_value: Fetches values from nested dictionaries using a
    key path.

Dependencies:

    asyncio: For asynchronous operations during metadata resolution.
    bluesky.preprocessors: For plan manipulation and metadata injection.
    bluesky.run_engine.Msg: For working with Bluesky plans.
    enum: For defining metadata types as an enumeration.
    typing: For type hints (e.g., Callable, Dict).
    bluesky_nexus: Constants and device model utilities for NeXus metadata
    handling.
"""

from enum import Enum, auto
from typing import Any, Callable, Dict, Generator, Union

import bluesky.plan_stubs as bps
from bluesky.preprocessors import SupplementalData, inject_md_wrapper

from bluesky_nexus.bluesky_nexus_const import (
    DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME,
    DEVICE_MD_KEY,
    NOT_AVAILABLE_LABEL,
    NX_MD_KEY,
    PRE_RUN_CPT_LABEL,
    PRE_RUN_MD_LABEL,
)
from bluesky_nexus.bluesky_nexus_device_model import (
    assign_pydantic_model_instance,
)
from bluesky_nexus.common.decorator_utils import measure_time
from bluesky_nexus.common.logging_utils import logger


# pylint: disable=too-few-public-methods
class SupplementalMetadata(SupplementalData):
    """Supplemental metadata.

    A class to manage and inject supplemental metadata into a Bluesky
    plan.

    This class checks the devices participating in the plan (run +
    baseline + silent) and generates metadata for the specified type
    (DEVICE_MD or NEXUS_MD). It ensures that devices in the
    'devices_dictionary' are either used in the run or are part of the
    baseline or silent devices, and injects metadata accordingly.
    """

    class MetadataType(Enum):
        """Metadata enums."""

        DEVICE_MD = auto()
        NEXUS_MD = auto()

    def __init__(
        self,
        devices_dictionary: dict | None = None,
        md_type: MetadataType | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the SupplementalMetadata instance.

        This constructor accepts both positional and keyword arguments,
        passing them to the parent class constructor.

        Args:
            *args: Positional arguments passed to the parent constructor.
            devices_dictionary: Dictionary of devices for metadata injection.
            Defaults to None.
            md_type: Metadata type (DEVICE_MD or NEXUS_MD). Defaults to None.
            **kwargs: Keyword arguments passed to the parent constructor.
        """
        super().__init__(*args, **kwargs)
        self.devices_dictionary: dict | None = devices_dictionary
        self.md_type: SupplementalMetadata.MetadataType | None = md_type

    def __call__(self, plan: Any):
        """Call.

        Delegate the call to the `inject_metadata_to_plan`function.
        """
        return (yield from self.inject_metadata_to_plan(plan))

    def inject_metadata_to_plan(
        self, plan: Generator[Any, Any, Any]
    ) -> Generator[Any, Any, Any]:
        """Inject metadata into a Bluesky plan.

        Injection is based on the configured type.

        Validates required attributes, selects the appropriate metadata
        creation function, gathers relevant devices, and injects metadata
        into the plan.

        Args:
            plan: A Bluesky plan generator.

        Returns:
            A generator with metadata injected.

        Raises:
            AttributeError: If required attributes are missing.
            ValueError: If the metadata type is invalid.
        """
        if self.devices_dictionary is None:
            raise AttributeError(
                "'devices_dictionary' must not be None when calling the instance."
            )

        if self.md_type is None:
            raise AttributeError(
                "'md_type' must not be None when calling the instance."
            )

        # Dictionary to map MetadataType to their respective
        # metadata creation functions
        metadata_functions = {
            self.MetadataType.DEVICE_MD: create_device_md,
            self.MetadataType.NEXUS_MD: create_nexus_md,
        }

        # Retrieve the correct function based on md_type
        create_md = metadata_functions.get(self.md_type)
        if create_md is None:
            raise ValueError(f"Invalid metadata type: {self.md_type}")

        # Assign to all the devices contained in 'devices_dictionary'
        # instances of pydantic models
        if self.MetadataType.NEXUS_MD == self.md_type:
            assign_pydantic_model_instance(self.devices_dictionary)

        # Create metadata and inject it into the plan
        metadata: dict = create_md(self.devices_dictionary)

        if isinstance(metadata, Generator):
            metadata = (yield from metadata) or {}

        mutated_plan = inject_md_wrapper(plan, metadata)
        return (yield from mutated_plan)


def extract_device_md(device: Any) -> dict:
    """Extract metadata from a device instance.

    Supported metadata containers:
    - ``md.get_attributes()`` (legacy / happi-compatible)
    - ``md`` as ``dict``
    - ``md`` as ``SimpleNamespace`` or any object exposing ``__dict__``
    """
    if not hasattr(device, "md"):
        raise AttributeError(f"Device {device} has no 'md' attribute")

    md = device.md

    # Preferred, explicit interface
    if hasattr(md, "get_attributes") and callable(md.get_attributes):
        return md.get_attributes()

    # Dict-style metadata
    if isinstance(md, dict):
        return md

    # Namespace / object metadata
    if hasattr(md, "__dict__"):
        return dict(md.__dict__)

    raise TypeError(
        f"Unsupported metadata container type for device.md: {type(md).__name__}"
    )


# Create device metadata
@measure_time
def create_device_md(devices_dictionary: dict) -> dict:
    """Create device metadata.

    Generate a device metadata dictionary for a collection of device
    instances.

    Metadata is extracted using a backward-compatible strategy that
    supports legacy ``md.get_attributes()``, dictionary-based metadata,
    and namespace-style metadata objects.

    Args:
        devices_dictionary (dict): A dictionary where keys are device names or
            identifiers and values are device instances. Each device instance
            is expected to have an `md` attribute.

    Returns:
        dict: A dictionary containing all device metadata under a top-level
        key specified by `metadata_key` ("device_md"). The structure is as
            follows:
            {
                "device_md": {
                    device_name_1: metadata_from_device_1,
                    device_name_2: metadata_from_device_2,
                    ...
                }
            }

    Example:
        devices = {
            "device1": device1_instance,
            "device2": device2_instance,
            ...
        }

        device_metadata = create_device_md(devices)
        # device_metadata would be structured with metadata from each device.

    Notes:
        - The function `create_metadata` is used to handle the metadata
          extraction and structuring.
        - This function assumes that `devices_dictionary` is well-formed
        - Devices must expose an ``md`` attribute; unsupported metadata containers
          raise a clear error.
    """
    # The extraction of the md dict from device instance
    metadata_key: str = DEVICE_MD_KEY
    return create_metadata(
        devices_dictionary,
        extract_device_md,
        metadata_key,
    )


# Create nexus metadata
@measure_time
def create_nexus_md(devices_dictionary: dict) -> Generator[None, None, dict]:
    """Create nexus metadata.

    Generate a metadata dictionary with resolved placeholders for a
    set of devices.

    This function constructs initial metadata, resolves any placeholders
    within the metadata (yielding intermediate results during resolution),
    and returns the final cleaned metadata dictionary. If a placeholder
    cannot be resolved, its containing NXfield is removed.

    Args:
        devices_dictionary (dict): A dictionary mapping device names to device
                                   instances.

    Yields:
        Any: Intermediate results from the placeholder resolution process.

    Returns:
        dict: The final metadata dictionary after all placeholders have been
              resolved and unresolved entries have been removed.
    """
    metadata_key: str = NX_MD_KEY

    def get_nx_model_metadata(device):
        if not hasattr(device, DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME):
            raise AttributeError(
                f"Device {device.name} does not have "
                f"{DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME} attribute."
            )
        return getattr(device, DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME).model_dump(
            exclude_none=True
        )

    metadata: dict = create_metadata(
        devices_dictionary,
        get_nx_model_metadata,
        metadata_key,
    )

    # Resolve placeholders in metadata
    yield from resolve_pre_run_placeholders(metadata[metadata_key], devices_dictionary)

    # Remove parent keys of: "value":NOT_AVAILABLE_LABEL.
    # This is the case if component value could not be read.
    metadata = process_value_not_available(metadata)

    return metadata


def create_metadata(
    devices_dictionary: Dict[str, Any],
    extract_fn: Callable,
    metadata_key: str,
) -> dict:
    """Generalized function to create metadata for devices.

    It is using the provided extraction function.

    Args:
        devices_dictionary (dict): A dictionary mapping device instance names
        to device instances objects.
        extract_fn (function): A function to extract metadata from a device.
        metadata_key (str): The key to be used for storing the metadata in the
            dictionary.

    Returns:
        dict: A dictionary containing the metadata, structured as follows:
            {
                metadata_key: {
                    "<device_name>": <metadata>,
                    ...
                }
            }
    """
    metadata: dict = {metadata_key: {}}
    for device_name, device_obj in devices_dictionary.items():
        metadata[metadata_key][device_name] = extract_fn(device_obj)
    return metadata


def process_value_not_available(data: dict) -> dict:
    """Recursively remove parent dictionaries.

    Remove parent directories that contain 'value': NOT_AVAILABLE_LABEL.
    """
    # Iterate over a copy of the dictionary items
    for key in list(data.keys()):
        value = data[key]

        # If the current value is a dictionary, check its contents
        if isinstance(value, dict):
            # If 'value': NOT_AVAILABLE_LABEL is in this dictionary,
            # mark the parent key for deletion
            if NOT_AVAILABLE_LABEL == value.get("value"):
                logger.warning("The key: '%s' removed from nexus metadata.", key)
                del data[key]
            else:
                # Otherwise, recursively check deeper levels
                data[key] = process_value_not_available(value)
    return data


def resolve_pre_run_placeholders(
    metadata: dict, devices_dictionary: dict[str, Any]
) -> Generator[None, None, None]:
    """Resolve pre run placeholders.

    Recursively resolve all $pre-run placeholders in a metadata
    dictionary for each device. If a placeholder cannot be resolved,
    removes the entire NXfield containing it.

    Args:
        metadata (dict): A dictionary containing metadata for each device,
        with device instance names as keys and sub-dictionaries containing
        metadata.
        devices_dictionary (dict): A dictionary mapping device instance names
            to device instances.
    """
    for device_name, device_metadata in metadata.items():
        # Get the device instance object by device name
        device_obj = devices_dictionary.get(device_name)

        # Recursively resolve placeholders in the device's metadata dictionary
        yield from _resolve_pre_run_placeholders_for_device(device_metadata, device_obj)


def _resolve_pre_run_placeholders_for_device(
    device_metadata: dict, device_obj: Any
) -> Generator[None, None, None]:
    """Resolve pre run placeholders for device.

    Helper function to recursively resolve $pre-run placeholders in
    the metadata dictionary for a specific device. If a placeholder
    cannot be resolved, removes the entire NXfield.

    Args:
        device_metadata (dict): Metadata dictionary for a specific device
            instance object.
        device_obj (Any): The device instance object associated with the
            current metadata.
    """
    for key, value in device_metadata.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            yield from _resolve_pre_run_placeholders_for_device(value, device_obj)
        elif isinstance(value, str) and (
            value.startswith(PRE_RUN_CPT_LABEL) or value.startswith(PRE_RUN_MD_LABEL)
        ):
            # Attempt to resolve the placeholder
            device_metadata[key] = yield from resolve_pre_run_placeholder_value(
                value, device_obj
            )


def resolve_pre_run_placeholder_value(placeholder: str, device_obj: Any) -> Any:
    """Resolve pre run placeholder value.

    Resolve a $pre-run-cpt or $pre-run-md placeholder for a specific
    device by dynamically fetching a nested component value.

    Args:
        placeholder (str): The placeholder string, e.g.
            "$pre-run-cpt:obj1: ... objN-1:objN:component". This is a chain
            telling how to access a component of a device instance.
            Delimiter is ':'. "$pre-run-md:key1: ... keyN-1:keyN".
            This is the chain telling how to access the key in a nested
            dictionary accessible over attribute md of the device instance.
            Delimiter is ':'. device_obj: The device instance to use for
            resolving the placeholder.

    Returns:
        The resolved value retrieved from the nested component path.

    Raises:
        AttributeError: If the component cannot be found or does not have a
            valid accessor.
    """
    placeholder_splitted: list = placeholder.split(":")
    prefix: str = placeholder_splitted[0]

    # Get the nested path, ignoring "$pre-run-cpt" or "$pre-run-md" prefix
    parts: list = placeholder_splitted[
        1:
    ]  # Ignore the "$pre-run-cpt" or "$pre-run-md" part

    # Resolve placeholder by asking device instance metadata for its value
    if PRE_RUN_MD_LABEL == prefix:
        if not parts:
            raise ValueError(
                f"Invalid placeholder format: {placeholder} detected in a "
                f"schema yml file associated with the device instance: "
                f"{device_obj.name}. Valid placeholder structure: "
                f"'$pre-run-md:key1: ... keyN-1:keyN'"
            )
        data: dict = extract_device_md(device_obj)
        value = get_nested_dict_value(data, parts)
        if value is None:
            logger.warning(
                "The key (key sequence) '%s' not found in the metadata "
                "of the device instance: '%s'. "
                "The associated NeXus metadata will be automatically removed.",
                ":".join(parts),
                device_obj.name,
            )

            return NOT_AVAILABLE_LABEL
        return value

    # Resolve placeholder by asking device instance component for its value
    if PRE_RUN_CPT_LABEL == prefix:
        # Navigate through the component path within the device instance
        component = device_obj
        for attribute in parts:
            component = getattr(component, attribute, None)
            if component is None:
                logger.warning(
                    "Attribute '%s' not found in device instance '%s'. "
                    "The associated NeXus metadata will be automatically removed.",
                    ".".join(parts),
                    device_obj.name,
                )
                return NOT_AVAILABLE_LABEL

        # Read the value from the component
        return (yield from bps.rd(component))

    raise ValueError(
        f"Invalid prefix: '{prefix}' found in the placeholder: "
        f"'{placeholder}'. Valid placeholder structure: "
        f"'$pre-run-md:key1: ... keyN-1:keyN' or "
        f"'$pre-run-cpt:obj1: ... objN-1:objN'"
    )


def get_nested_dict_value(
    current_level: dict[str, Any], key_path: list[str]
) -> Union[Any, None]:
    """Get nested dict value.

    Retrieve the value of a nested dictionary based on a list of keys
    representing the path.

    Args:
        current_level (dict): The nested dictionary to search.
        key_path (list): A list of keys representing the path to the desired
            value. Each key corresponds to a level in the nested dictionary.

    Returns:
        The value associated with the final key in `key_path` if the path is
        valid, or `None` if any key is missing.

    Example:
        current_level = {
            "a": {
                "b": {
                    "c": 42
                }
            }
        }

        key_path = ["a", "b", "c"]
        result = get_nested_value(current_level, key_path)  # Returns 42
    """
    for key in key_path:
        if isinstance(current_level, dict) and key in current_level:
            current_level = current_level[key]
        else:
            return None  # Return None if the path is invalid
    return current_level
