"""
Module: nx_models.

Defines and maps models used in the NeXus data format within the
Bluesky Nexus framework.

This module provides a collection of classes that represent various
components of a scientific experiment setup, including detectors,
general configurations, monochromators, and more. These models
facilitate the organization of metadata and experimental data.

It contains a function to validate that a dictionary schema is
against all the ones defined in this package.
"""

from pprint import pformat

from .nx_detector_group_model import NXdetector_groupModel
from .nx_detector_model import NXdetectorModel
from .nx_general_model import NXgeneralModel
from .nx_monitor_model import NXmonitorModel
from .nx_monochromator_model import NXmonochromatorModel
from .nx_positioner_model import NXpositionerModel

# Define a mapping between model name and model class name
MODEL_NAME_TO_CLASS_MAPPING = {
    "NXdetectorModel": NXdetectorModel,
    "NXgeneralModel": NXgeneralModel,
    "NXmonochromatorModel": NXmonochromatorModel,
    "NXpositionerModel": NXpositionerModel,
    "NXmonitorModel": NXmonitorModel,
    "NXdetector_groupModel": NXdetector_groupModel,
}


def validate_schema(schema: dict) -> None:
    """Will validate a dictionary schema assuming it is in this package."""

    if "nxmodel" not in schema:
        raise TypeError("`nxmodel` not in schema this is a required field.")

    nx_model = schema["nxmodel"]
    if schema["nxmodel"] not in MODEL_NAME_TO_CLASS_MAPPING:
        raise TypeError(
            f"Cannot validate nxmodel `{nx_model}` as it doesn't have a schema."
            f"available schema are\n{pformat(list(MODEL_NAME_TO_CLASS_MAPPING))}"
        )

    MODEL_NAME_TO_CLASS_MAPPING[nx_model].validate(schema)
