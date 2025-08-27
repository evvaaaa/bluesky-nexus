"""
Module: nx_data_model.py.

This module defines the Pydantic model for the NXdata group in the NeXus
format. NXdata is a core component of NeXus files used to store plottable
scientific data along with its associated axes, attributes, and metadata.

The NXdataModel class structures and validates the contents of an NXdata
group, ensuring compliance with NeXus conventions.

Classes:
- NXdataModel: Represents an NXdata group with plottable data, axes, and
    attributes.
- NXdataModel.AttributesModel: Defines NXdata attributes, such as signal,
    axes, and default slice.
- NXdataModel.AXISNAMEModel: Represents coordinate values along one or more
    data dimensions.
- NXdataModel.DATAModel: Stores the actual numerical data for visualization
    and analysis.

Key Features:
- Supports signal and auxiliary signal definitions for data visualization.
- Handles data axes and their relationships via metadata attributes.
- Incorporates error values, scaling factors, and offsets for numerical
    accuracy.
- Ensures NeXus compliance through structured validation.
"""

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    BaseModel,
    ConfigDict,
    Field,
    NXfieldModelForAttribute,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


class NXdataModel(NXgroupModel):
    """NXdataModel.

    Represents an NXdata group in the NeXus format. The NXdata group
    contains plottable scientific data along with its associated axes,
    attributes, and metadata. This class structures and validates the
    contents of the NXdata group to ensure compliance with NeXus
    conventions.

    Attributes:
        attributes (Optional[AttributesModel]): Attributes specific to the
        NXdata group, such as signal, auxiliary signals, default slice, and
        axes.
        AXISNAME (Optional[AXISNAMEModel]): Coordinate values along one or
        more data dimensions.
        DATA (Optional[DATAModel]): Data values to be used as plottable data.
        FIELDNAME_errors (Optional[NXfieldModelWithPrePostRunString]): Errors
            (uncertainties or standard deviations) associated with any field
            in the NXdata group.
        scaling_factor (Optional[NXfieldModelWithPrePostRunString]): Scaling
        factor for data values to obtain physical values.
        offset (Optional[NXfieldModelWithPrePostRunString]): Optional offset
        to apply to the data values.
        title (Optional[NXfieldModelWithPrePostRunString]): Title for the
        plot.
        x (Optional[NXfieldModelWithPrePostRunString]): Array of x-axis values
        for the plot.
        y (Optional[NXfieldModelWithPrePostRunString]): Array of y-axis values
        for the plot.
        z (Optional[NXfieldModelWithPrePostRunString]): Array of z-axis values
        for the plot.
    """

    # ----- Define attributes of the NXData group -----
    class AttributesModel(BaseModel):
        """AttributesModel.

        Represents the attributes of the NXdata group, including
        signal, auxiliary signals, default slice, and axes definitions.

        Attributes:
            signal (Optional[NXfieldModelForAttribute]): The name of the
            signal that contains the default plottable data.
            auxiliary_signals (Optional[NXfieldModelForAttribute]): Names of
            additional signals to be plotted with the default signal.
            default_slice (Optional[NXfieldModelForAttribute]): The slice of
            data to show in a plot by default.
            AXISNAME_indices (Optional[NXfieldModelForAttribute]): Indices
            defining which data dimensions are spanned by the corresponding
            axis.
            axes (Optional[NXfieldModelForAttribute]): Names of the AXISNAME
            fields that contain the values of the coordinates along the data
            dimensions.
        """

        signal: Optional[NXfieldModelForAttribute] = Field(
            None,
            description="The value is the name of the signal that contains "
            "the default plottable data.",
        )
        auxiliary_signals: Optional[NXfieldModelForAttribute] = Field(
            None,
            description="Array of strings holding the names of additional "
            "signals to be plotted with the default signal. ",
        )
        default_slice: Optional[NXfieldModelForAttribute] = Field(
            None,
            description="Which slice of data to show in a plot by default.",
        )
        AXISNAME_indices: Optional[NXfieldModelForAttribute] = Field(
            None,
            description="The AXISNAME_indices attribute is a single integer "
            "or an array of integers that defines which data dimension(s) are "
            "spanned by the corresponding axis. The first dimension index is "
            "0 (zero).",
        )
        axes: Optional[NXfieldModelForAttribute] = Field(
            None,
            description="The axes attribute is a list of strings which are "
            "the names of the AXISNAME fields that contain the values of"
            "the coordinates along the data dimensions.",
        )
        model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    attributes: Optional[AttributesModel] = Field(
        None, description="Attributes specific to the 'NXdata' group."
    )

    # ----- AXISNAME -----
    class AXISNAMEModel(NXfieldModelWithPrePostRunString):
        """AXISNAMEModel.

        Represents coordinate values along one or more data
        dimensions. The AXISNAME model includes attributes like axis
        label, units, distribution, and indices for the first and last
        good values along the axis.

        Attributes:
            attributes (Optional[AttributesModel]): Attributes specific to
            the AXISNAME field, including long name, units, and distribution.
        """

        class AttributesModel(BaseModel):
            """AttributesModel.

            Defines the attributes for the AXISNAME field, including
            long name, units, distribution, and indices for valid data
            points.

            Attributes:
                long_name (Optional[NXfieldModelForAttribute]): Axis label.
                units (Optional[NXfieldModelForAttribute]): Units for the
                coordinate values.
                distribution (Optional[NXfieldModelForAttribute]): Whether the
                axis has a single or multiple values.
                first_good (Optional[NXfieldModelForAttribute]): Index of the
                first valid coordinate value.
                last_good (Optional[NXfieldModelForAttribute]): Index of the
                last valid coordinate value.
                axis (Optional[NXfieldModelForAttribute]): Index identifying
                this specific axis.
            """

            long_name: Optional[NXfieldModelForAttribute] = Field(
                None, description="Axis label"
            )
            units: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="Unit in which the coordinate values are " "expressed",
            )
            distribution: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="0|false: single value, 1|true: multiple values",
            )
            first_good: Optional[NXfieldModelForAttribute] = Field(
                None, description="Index of first good value"
            )
            last_good: Optional[NXfieldModelForAttribute] = Field(
                None, description="Index of last good value"
            )
            axis: Optional[NXfieldModelForAttribute] = Field(
                None,
                gt=0,
                description="Index (positive integer) identifying this "
                "specific set of numbers.",
            )
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

        attributes: Optional[AttributesModel] = Field(
            None, description="Attributes specific to the 'AXISNAME' field."
        )

    AXISNAME: Optional[AXISNAMEModel] = Field(
        None,
        description="Coordinate values along one or more data dimensions.",
    )

    # ----- DATA -----
    class DATAModel(NXfieldModelWithPrePostRunString):
        """DATAModel.

        Represents the actual numerical data for visualization and
        analysis in the NXdata group. This class contains attributes
        like signal, axes, and long name for the data.

        Attributes:
            attributes (Optional[AttributesModel]): Attributes specific to
            the DATA field, including signal and axes.
        """

        class AttributesModel(BaseModel):
            """AttributesModel.

            Defines the attributes for the DATA field, such as the
            signal, axes, and data label.

            Attributes:
                signal (Optional[NXfieldModelForAttribute]): The signal to be
                    plotted (independent axis).
                axes (Optional[NXfieldModelForAttribute]): Names of the
                    coordinates (independent axes) for this data set.
                long_name (Optional[NXfieldModelForAttribute]): Label for the
                    data.
            """

            signal: Optional[NXfieldModelForAttribute] = Field(
                None,
                gt=0,
                description="Plottable (independent) axis, indicate index " "number.",
            )
            axes: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="Defines the names of the coordinates "
                "(independent axes) for this data set as a "
                "colon-delimited array.",
            )
            long_name: Optional[NXfieldModelForAttribute] = Field(
                None, description="Data label."
            )
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

        attributes: Optional[AttributesModel] = Field(
            None, description="Attributes specific to the 'DATA' field."
        )

    DATA: Optional[DATAModel] = Field(
        None,
        description="Data values to be used as the NeXus plottable " "data.",
    )
    FIELDNAME_errors: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="'Errors' (meaning uncertainties or standard deviations) "
        "associated with any field named FIELDNAME in this NXdata group "
        "(e.g. an axis, signal or auxiliary signal).",
    )
    scaling_factor: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="The elements in data are usually float values really. "
        "For efficiency reasons these are usually stored as integers after "
        "scaling with a scale factor. This value is the scale factor. "
        "It is required to get the actual physical value, when necessary.",
    )
    offset: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="An optional offset to apply to the values in data."
    )
    title: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Title for the plot."
    )
    x: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Array of x-axis values for the plot."
    )
    y: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Array of y-axis values for the plot."
    )
    z: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Array of z-axis values for the plot."
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
