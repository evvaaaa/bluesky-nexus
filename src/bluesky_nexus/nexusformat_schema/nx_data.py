"""Contains the definition for NXdata."""

from typing import Self

from pydantic import model_validator

from bluesky_nexus.base_schema import (
    NxAttribute,
    NxConstantAttribute,
    NxField,
    add_nx_class_basemodel,
)

from .nx_object import NxObject


@add_nx_class_basemodel
class NxData(NxObject):
    """Represents a NeXus NXdata.

    For the implementation in bluesky nexus, signal and axes
    must be specified as constant NxAttributes, e.g

    $signal: "some_data_signal"
    $axes: [some_axis_name_1, some_axis_name_2]
    some_data_signal: some_data_key
    some_axis_name_1: another_data_key
    some_axis_name_2: yet_another_data_key
    """

    signal: NxConstantAttribute[str]
    """The name of the signal that contains the default plottable data.
    While not specifically required in Nxdata, we have made it required
    in the nexus writer."""

    axes: NxConstantAttribute[list[str]]
    """The axes attribute is a list of strings which are the names of the
    AXISNAME fields to be used as the default axis along every DATA dimension"""

    auxillary_signals: NxConstantAttribute[list[str]] | None = None
    """Array of strings holding the names of additional signals
    to be plotted with the default signal."""

    default_slice: NxAttribute | None = None
    """Which slice of data to show in a plot by default. This is useful
    especially for datasets with more than 2 dimensions."""

    title: NxAttribute | None = None
    """Title for the plot."""

    @model_validator(mode="after")
    def _check_data_and_axes_present(self) -> Self:
        signal = self.signal.constant
        axes = self.axes.constant

        signal_field = getattr(self, signal, None)
        if signal_field is None:
            raise ValueError(
                f"Specified a signal {signal} as the NxData signal attribute "
                f"but no signal field of this name was provided."
            )

        if not isinstance(signal_field, NxField):
            raise ValueError(
                f"NxData signal attribute {signal}: {signal_field} exists "
                "but it is not of type NxField."
            )

        for axis in axes:
            axis_field = getattr(self, axis, None)
            if axis_field is None:
                raise ValueError(
                    f"Specified an axis {axis} in the NxData axes attribute "
                    f"but no axis field of this name was provided."
                )
            if not isinstance(axis_field, NxField):
                raise ValueError(
                    f"NxData axis attribute {axis}: {axis_field} exists "
                    "but it is not of type NxField."
                )

        return self
