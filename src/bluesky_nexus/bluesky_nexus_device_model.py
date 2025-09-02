"""
Module: bluesky_nexus_device_model.

Handles the instantiation and assignment of Pydantic models to device
instances within the Bluesky Nexus framework.

This module enables dynamic creation of Pydantic model instances based
on schema files and assigns each instance to the `nx_model` attribute
of a device object. It also provides utilities for reading device
attributes and managing schema-related errors.

Functions
---------
assign_pydantic_model_instance(devices_dictionary: dict)
    Assigns a Pydantic model instance to each device in the given
    dictionary based on the schema associated with the device.

create_model_instance(model_name: str, schema_content: dict) -> object
    Creates a Pydantic model instance by mapping the model name to the
    corresponding Pydantic class and initializing it with the provided
    schema content.

read_attribute(device, attribute_name: str)
    Retrieves the value of a specified attribute from a device. Returns
    None and logs an error if the attribute does not exist.

Modules and Constants
---------------------
Includes various utilities, constants, and models related to NeXus
schema and device management, such as
`DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME` and Pydantic models.

Error Handling
--------------
Raises `ValueError` for missing or invalid schema files, missing keys
in schemas, or unrecognized model names.
"""

import json

from bluesky_nexus.bluesky_nexus_const import (
    DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME,
    DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME,
    NX_SCHEMA_MODEL_NAME_KEY,
)
from bluesky_nexus.common.logging_utils import (
    logger,
)
from bluesky_nexus.models.nx_models import (
    MODEL_NAME_TO_CLASS_MAPPING,
)


def assign_pydantic_model_instance(
    devices_dictionary: dict,
):
    """assign_pydantic_model_instance.

    Assign a Pydantic model instance to each device in the dictionary.
    """
    if not devices_dictionary:
        logger.warning(
            "Assignment of pydantic model instances to devices "
            "is not possible since 'devices_dictionary' is empty."
        )

    for dev_instance in devices_dictionary.values():
        # Each device instance has a schema content that is assigned
        # to it as a attribute 'nx_schema'
        schema_content: dict = read_attribute(
            dev_instance,
            DEVICE_CLASS_NX_SCHEMA_ATTRIBUTE_NAME,
        )

        # When pydantic schema is not assigned to the class
        # of the dev_instance (by means of the decorator)
        # Triggers for schema_content = None or "" (empty string) or
        # [] (empty list) or {} (empty dict) or 0, 0.0 or False
        if not schema_content:
            schema_content = {
                "nx_model": "NXgeneralModel",
                "nxclass": f"NX{dev_instance.__class__.__name__.lower()}",
            }
            # Convert dictionary to JSON string
            schema_content_str: str = json.dumps(schema_content)
            logger.warning(
                "Pydantic NeXus schema content for device: '%s' was None or empty. "
                "Defaulting to: %s",
                dev_instance.name,
                schema_content_str,
            )

        else:
            logger.debug(
                "Pydantic NeXus schema content for device: '%s' found as expected "
                "(it is not None or not empty).",
                dev_instance.name,
            )

        # Read model name from the schema content
        try:
            model_name = schema_content[NX_SCHEMA_MODEL_NAME_KEY]
        except KeyError as err:
            raise ValueError(
                f"The key: {NX_SCHEMA_MODEL_NAME_KEY} not found "
                f"in a schema file associated with "
                f"the device: {dev_instance.name}"
            ) from err

        # Create instance of the pydantic model
        model_instance: object = create_model_instance(
            model_name,
            schema_content,
        )

        # Dynamically assign the attribute to the object
        setattr(
            dev_instance,
            DEVICE_INSTANCE_NX_MODEL_ATTRIBUTE_NAME,
            model_instance,
        )


def create_model_instance(
    model_name,
    schema_content,
) -> object:
    """create_model_instance.

    Create a model instance based on the model name and schema
    content.

    Returns
    -------
    object
        The instantiated model.
    """
    # Check if the model_name corresponds to one of the classes in the mapping
    if model_name in MODEL_NAME_TO_CLASS_MAPPING:
        # Instantiate the model class.
        # **schema_content unpacks the dictionary schema_content
        # and passes each key-value pair as keyword arguments
        # to the constructor of the class.
        model_instance: object = MODEL_NAME_TO_CLASS_MAPPING[model_name](
            **schema_content
        )
        return model_instance

    raise ValueError(
        f"Class with name {model_name} not found in "
        f"MODEL_NAME_TO_CLASS_MAPPING! Check the content "
        f" of 'MODEL_NAME_TO_CLASS_MAPPING' in the file: "
        f"'bluesky_nexus.models.nx_models'"
    )


def read_attribute(
    device,
    attribute_name,
):
    """Read the value of a specified attribute from a device instance.

    Parameters
    ----------
    device : object
        The device instance.
    attribute_name : str
        The name of the attribute to read.

    Returns
    -------
    Any
        The value of the attribute if it exists, otherwise None.
    """
    try:
        # Attempt to retrieve the attribute's value
        value = getattr(
            device,
            attribute_name,
        )
        return value
    except AttributeError:
        # Handle case where the attribute does not exist
        logger.warning(
            "Attribute '%s' does not exist on the device %s.",
            attribute_name,
            device.name,
        )
        return None
