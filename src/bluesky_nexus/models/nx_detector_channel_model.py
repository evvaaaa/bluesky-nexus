"""
Module: nx_detector_channel_model.py.

This module defines the Pydantic model for the NXdetector_channel group in
the NeXus format. The NXdetector_channel group is used to store data related
to individual detector channels, including threshold energy, flat field
correction, pixel masks, and saturation values.

The NXdetector_channelModel class structures and validates the contents of an
NXdetector_channel group to ensure compliance with NeXus conventions.

Classes:
- NXdetector_channelModel: Represents an individual detector channel with
  properties related to energy thresholds, corrections, and data validity.

Key Features:
- Supports threshold energy definition for photon detection.
- Includes fields for flat field correction and pixel masks.
- Stores saturation and underload values to define the valid measurement
  range.
- Ensures structured validation for NeXus compliance.
"""

# pylint: disable=duplicate-code

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    ConfigDict,
    Field,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


# pylint: disable=invalid-name
class NXdetector_channelModel(NXgroupModel):
    """Represents an NXdetector_channel group in the NeXus format.

    This group stores metadata and calibration information for an individual
    detector channel, including threshold energy, flat field correction,
    pixel masks, and saturation limits.

    Attributes:
        threshold_energy (Optional[NXfieldModelWithPrePostRunString]):
            The energy threshold at which a photon will be recorded.
        flatfield_applied (Optional[NXfieldModelWithPrePostRunString]):
            Indicates whether the flat field correction has been applied in
            the electronics (True or False).
        flatfield (Optional[NXfieldModelWithPrePostRunString]):
            The response of each pixel given a constant input.
        flatfield_errors (Optional[NXfieldModelWithPrePostRunString]):
            Errors associated with the flat field correction data.
        pixel_mask_applied (Optional[NXfieldModelWithPrePostRunString]):
            Indicates whether the pixel mask correction has been applied in
            the electronics (True or False).
        pixel_mask (Optional[NXfieldModelWithPrePostRunString]):
            Custom pixel mask for this channel. May include nP as the first
            dimension for masks that vary for each scan point.
        saturation_value (Optional[NXfieldModelWithPrePostRunString]):
            The value at which the detector becomes saturated. Data above this
            value is considered invalid.
        underload_value (Optional[NXfieldModelWithPrePostRunString]):
            The lowest value at which pixels for this detector would be
            reasonably measured. Data below this value is considered invalid.
    """

    threshold_energy: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Energy at which a photon will be recorded."
    )
    flatfield_applied: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="True when the flat field correction has been applied in "
        "the electronics, false otherwise.",
    )
    flatfield: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Response of each pixel given a constant input."
    )
    flatfield_errors: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Errors of the flat field correction data. The form "
        "flatfield_error is deprecated.",
    )
    pixel_mask_applied: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="True when the pixel mask correction has been applied in "
        "the electronics, false otherwise.",
    )
    pixel_mask: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Custom pixel mask for this channel. May include nP as "
        "the first dimension for masks that vary for each scan point.",
    )
    saturation_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="The value at which the detector goes into saturation. "
        "Especially common to CCD detectors, the data is known to be "
        "invalid above this value.",
    )
    underload_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="The lowest value at which pixels for this detector "
        "would be reasonably measured. The data is known to be invalid "
        "below this value.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
