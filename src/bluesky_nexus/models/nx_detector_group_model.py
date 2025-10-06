"""
nx_detector_group_model: Model for managing logical groupings of detectors.

This module defines a model that organizes and manages metadata for logical
groupings of detectors in a NeXus-compliant format. It includes attributes for
describing group names, indices, parent-child hierarchies, and group types.
"""

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


# pylint: disable=invalid-name
class NXdetector_groupModel(NXgroupModel):
    """Model for managing logical groupings of detectors.

    This class organizes and manages metadata for logical groupings of
    detectors, including hierarchical relationships, group names, and unique
    identifiers.

    Attributes:
        default (NXattrModel): Default attribute, declares which child group
            contains a path leading to the default data to be plotted.
        group_names (Optional[NXfieldModelWithPrePostRunString]): An array of
        the names of the detectors or hierarchical groupings of detectors.
        group_index (Optional[NXfieldModelWithPrePostRunString]): An array of
            unique identifiers for detectors or groupings of detectors.
        group_parent (Optional[NXfieldModelWithPrePostRunString]): An array of
        the hierarchical levels of the parents of detectors or groupings.
        group_type (Optional[NXfieldModelWithPrePostRunString]): Code number
        for group type, e.g., bank=1, tube=2, etc.
    """

    default: NXattrModel = Field(
        NXattrModel(value="group_names"),
        description="Declares which child group contains a path leading to "
        "the default data to be plotted.",
    )
    group_names: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="An array of the names of the detectors or hierarchical "
        "groupings of detectors.",
    )
    group_index: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="An array of unique identifiers for detectors or "
        "groupings of detectors.",
    )
    group_parent: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="An array of the hierarchical levels of the parents of "
        "detectors or groupings.",
    )
    group_type: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Code number for group type, e.g., bank=1, tube=2, etc.",
    )
