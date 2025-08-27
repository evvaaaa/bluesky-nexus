"""nx_log_model.

Model for organizing and logging time-series data.

This module provides a model for handling time-series data logging in various
scientific or experimental contexts. It is designed to record time, value,
and associated metadata for logged entries, including raw and processed data.
Additionally, the model accommodates attributes such as uncertainty,
duration, and timestamps that relate the log to other components.

Class:
    - NXlogModel: A model for managing time-series data logs, with attributes
      for time, logged values, uncertainty, and other related metadata.
"""

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    BaseModel,
    ConfigDict,
    Field,
    NXattrModel,
    NXfieldModelForAttribute,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


class NXlogModel(NXgroupModel):
    """NXlogModel.

    Model for managing time-series data logs, including time, values,
    and metadata.

    This class provides a structure for organizing time-series data,
    including the time of each entry, the logged value (such as
    temperature), raw measurements, statistical aggregates (e.g.,
    averages, minimum and maximum values), and uncertainty information.
    The model also supports timestamps and cue indices for relating the
    logged data to external events or other measurements in the system.
    """

    default: NXattrModel = Field(NXattrModel(value="value"), description="Default")

    # ----- time -----
    # pylint: disable=invalid-name
    class timeModel(NXfieldModelWithPrePostRunString):
        """timeModel.

        Model for attributes related to time in the log.

        This class defines the time attributes for each logged entry,
        including the start time and the scaling factor that can be
        applied to the time values.
        """

        class AttributesModel(BaseModel):
            """AttributesModel."""

            start: Optional[NXfieldModelForAttribute] = Field(None)
            scaling_factor: Optional[NXfieldModelForAttribute] = Field(None)
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

        attributes: Optional[AttributesModel] = Field(
            None, description="Attributes specific to the 'time' field."
        )

    time: Optional[timeModel] = Field(
        None,
        description="Time of logged entry. The times are relative to the "
        "'start' attribute and in the units specified in the 'units' "
        "attribute. Please note that absolute timestamps under unix are "
        "relative to 1970-01-01T00:00:00.0Z.",
    )
    value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Array of logged value, such as temperature. If this is a "
        "single value the dimensionality is nEntries.",
    )
    raw_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Array of raw information, such as thermocouple voltage.",
    )
    description: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Description of logged value."
    )
    average_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Average of the logged values."
    )
    average_value_errors: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="estimated uncertainty (often used: standard deviation) "
        "of average_value.",
    )
    minimum_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Minimum recorded value."
    )
    maximum_value: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Maximum recorded value."
    )
    duration: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Total time log was taken."
    )

    class cue_timestamp_zeroModel(NXfieldModelWithPrePostRunString):
        """cue_timestamp_zeroModel.

        Model for attributes related to cue timestamps in the log.
        """

        class AttributesModel(BaseModel):
            """AttributesModel.

            Attributes for the 'cue_timestamp_zero' field, which defines
            the " "timestamps associated with the specific cue points in
            the logged " "data.
            """

            start: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="If missing start is assumed to be the same as "
                "for 'time'.",
            )
            scaling_factor: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="If missing start is assumed to be the same as "
                "for 'time'.",
            )
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

        attributes: Optional[AttributesModel] = Field(
            None,
            description="Attributes specific to the 'cue_timestamp_zero' " "field.",
        )

    cue_timestamp_zero: Optional[cue_timestamp_zeroModel] = Field(
        None,
        description="Timestamps matching the corresponding cue_index into the "
        "time, value pair.",
    )
    cue_index: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Index into the time, value pair matching the "
        "corresponding cue_timestamp_zero.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
