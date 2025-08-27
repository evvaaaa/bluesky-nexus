"""nx_positioner_model.

Model for managing positioner-related metadata and
configuration.

This module defines a model that organizes and manages metadata and
configuration specific to positioners in an experimental setup. It includes
attributes to describe movable systems such as motors and temperature
controllers. Example attributes include position, velocity, and
acceleration_time.

Classes:
    - NXpositionerModel: Model for managing positioner-related metadata and
      configuration.
"""

# pylint: disable=duplicate-code

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)
from bluesky_nexus.models.nx_transformations_model import (
    NXtransformationsModel,
)


class NXpositionerModel(NXgroupModel):
    """NXpositionerModel.

    Model for managing positioner-related metadata and configuration.

    This class organizes and manages metadata and configuration specific to
    positioners in an experimental setup. It allows for the inclusion of key
    attributes such as position, velocity, and acceleration_time related to the
    positioner component.

    Attributes:
        default (NXattrModel): Default attribute, typically for energy
        selection.
        name (Optional[NXfieldModelWithPrePostRunString]): Symbolic or mnemonic
            name (one word).
        description (Optional[NXfieldModelWithPrePostRunString]): Description
        of the positioner.
        value (Optional[NXfieldModelWithPrePostRunString]): Best known value of
            the positioner - need [n] as it may be scanned.
        raw_value (Optional[NXfieldModelWithPrePostRunString]): Raw value of
        the positioner - need [n] as it may be scanned.
        target_value (Optional[NXfieldModelWithPrePostRunString]): Targeted
            (commanded) value of the positioner - need [n] as it may be
            scanned.
        tolerance (Optional[NXfieldModelWithPrePostRunString]): Maximum
        allowable difference between target_value and value.
        soft_limit_min (Optional[NXfieldModelWithPrePostRunString]): Minimum
            allowed limit to set value.
        soft_limit_max (Optional[NXfieldModelWithPrePostRunString]): Maximum
            allowed limit to set value.
        velocity (Optional[NXfieldModelWithPrePostRunString]): Velocity of the
            positioner (distance moved per unit time).
        acceleration_time (Optional[NXfieldModelWithPrePostRunString]): Time to
            ramp the velocity up to full speed.
        controller_record (Optional[NXfieldModelWithPrePostRunString]):
        Hardware device record, e.g., EPICS process variable, taco/tango.
        depends_on (Optional[NXfieldModelWithPrePostRunString]): NeXus
        positions components by applying a set of translations and rotations.
        TRANSFORMATIONS (Optional[NXtransformationsModel]): This is the group
            recommended for holding the chain of translation and rotation
            operations necessary to position the component within the
            instrument.
    """

    default: NXattrModel = Field(NXattrModel(value="value"), description="Default.")
    name: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="symbolic or mnemonic name (one word)"
    )
    description: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="description of positioner"
    )
    value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="best known value of positioner - need [n] as may be " "scanned",
    )
    raw_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="raw value of positioner - need [n] as may be scanned",
    )
    target_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="targeted (commanded) value of positioner - need [n] as "
        "may be scanned",
    )
    tolerance: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="maximum allowable difference between target_value and " "value",
    )
    soft_limit_min: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="minimum allowed limit to set value"
    )
    soft_limit_max: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="maximum allowed limit to set value"
    )
    velocity: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="velocity of the positioner (distance moved per unit " "time)",
    )
    acceleration_time: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="time to ramp the velocity up to full speed"
    )
    controller_record: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Hardware device record, e.g. EPICS process variable, "
        "taco/tango...",
    )
    depends_on: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="NeXus positions components by apply a set of "
        "translations and rotations",
    )
    TRANSFORMATIONS: Optional[NXtransformationsModel] = Field(
        None,
        description="This is the group recommended for holding the chain of "
        "translation and rotation operations necessary to position the "
        "component within the instrument.",
    )
