"""
nx_general_model: General model for grouping metadata and configuration.

This module defines a general-purpose model for organizing and managing
metadata and configuration settings. It offers flexibility by allowing
arbitrary types and extra fields, making it adaptable for a variety of use
cases.

Class:
    - NXgeneralModel: A model for managing general metadata and flexible
    configuration.
"""

from .nx_core_models import (
    ConfigDict,
    NXgroupModel,
)


class NXgeneralModel(NXgroupModel):
    """General model for grouping metadata and configuration.

    This class provides a flexible structure for handling metadata and
    configuration attributes, allowing customization through an
    adaptable configuration model. The model configuration allows
    arbitrary types and extra fields to be included, offering
    flexibility for various types of metadata or attributes.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
