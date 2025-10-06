"""
Module: nx_models.

Defines and maps models used in the NeXus data format within the
Bluesky Nexus framework.

This module provides a collection of classes that represent various
components of a scientific experiment setup, including detectors,
general configurations, monochromators, and more. These models
facilitate the organization of metadata and experimental data.

Classes
-------
NXdetectorModel
    Represents detector-related metadata and configuration.

NXgeneralModel
    General-purpose model for grouping metadata and configuration.

NXmonochromatorModel
    Manages monochromator-related metadata and configuration.

NXpositionerModel
    Represents positioner-related metadata and configuration.

NXmonitorModel
    Represents monitor-related metadata and configuration.

NXdetector_groupModel
    Organizes a logical group of detectors in a scientific setup.

Mappings
--------
MODEL_NAME_TO_CLASS_MAPPING
    A dictionary mapping model names to their corresponding classes.
"""

from bluesky_nexus.models.nx_detector_group_model import NXdetector_groupModel
from bluesky_nexus.models.nx_detector_model import NXdetectorModel
from bluesky_nexus.models.nx_general_model import NXgeneralModel
from bluesky_nexus.models.nx_monitor_model import NXmonitorModel
from bluesky_nexus.models.nx_monochromator_model import NXmonochromatorModel
from bluesky_nexus.models.nx_positioner_model import NXpositionerModel

# Define a mapping between model name and model class name
MODEL_NAME_TO_CLASS_MAPPING = {
    "NXdetectorModel": NXdetectorModel,
    "NXgeneralModel": NXgeneralModel,
    "NXmonochromatorModel": NXmonochromatorModel,
    "NXpositionerModel": NXpositionerModel,
    "NXmonitorModel": NXmonitorModel,
    "NXdetector_groupModel": NXdetector_groupModel,
}
