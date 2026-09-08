"""Contains the definition for NXdata."""

from typing import Any, Self

from pydantic import model_serializer, model_validator

from bluesky_nexus.base_schema import (
    NxAttribute,
    NxConstantAttribute,
    NxField,
    add_nx_class_basemodel,
)
from bluesky_nexus.base_schema._nx_group import NxGroup
from bluesky_nexus.base_schema._nx_link import NxInternalLink

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

    @model_validator(mode="before")
    @classmethod
    def _prevent_scalar_string_axes(cls, value: dict) -> dict[str, Any]:
        """Stops e.g axes="axis1" -> axes=["a", "x", "i", "s", "1"]"""
        if (
            "axes" in value
            and "constant" in value["axes"]
            and isinstance(value["axes"]["constant"], str)
        ):
            pretty_key_value = {"axes": value["axes"]}
            raise TypeError(
                f"Received single string {pretty_key_value}, this should be an iterable of string."
            )
        return value

    @model_validator(mode="after")
    def _create_nx_links_into_signals(self) -> Self:
        """Creates `NxInternalLink`'s into signals to allow `NxLog` fields
        to be referenced"""

        if not hasattr(self, self.signal.constant) or not isinstance(
            getattr(self, self.signal.constant), NxField
        ):
            raise TypeError(
                f"Referenced signal `{self.signal.constant}` is not an NxField inside `NxData`."
            )

        signal_link = NxInternalLink(link=[self.signal.constant])
        if hasattr(self, "signal_link") and self.signal_link != signal_link:  # type: ignore
            raise TypeError(
                "Found field `signal_link` inside `NxData`. This field is reserved by "
                "bluesky-nexus to allow NxData to reference `NxLog`."
            )
        self.signal_link = signal_link
        # Change the signal reference attribute to point towards the new link.
        self.signal.constant = "signal_link"

        for axis_index, axis_name in enumerate(self.axes.constant):
            if not hasattr(self, axis_name) or not isinstance(getattr(self, axis_name), NxField):
                raise TypeError(
                    f"Referenced axis `{axis_name}` is not an NxField inside `NxData`."
                )
            axis_link_name = f"axis{axis_index}_link"
            axis_link = NxInternalLink(link=[axis_name])
            if hasattr(self, axis_link_name) and getattr(self, axis_link_name) != axis_link:
                raise TypeError(
                    f"Found field `{axis_link_name}` inside `NxData`. This field is reserved by "
                    "bluesky-nexus to allow NxData to reference `NxLog`."
                )
            setattr(self, axis_link_name, axis_link)
            # Change the axes reference attribute to point towards the new link
            self.axes.constant[axis_index] = axis_link_name

        return self

    @model_serializer()
    def _remove_signal_and_axes_nx_links(self) -> dict[str, Any]:
        serialized = NxGroup._use_shorthand_and_add_at_key_to_attributes(self)

        unlinked_axes = []
        for axis_field_link_name in [f"&{name}" for name in serialized["$axes"]]:
            # Index 0 since the signal is at the top level.
            unlinked_axes.append(serialized[axis_field_link_name][0])
            del serialized[axis_field_link_name]
        serialized["$axes"] = unlinked_axes

        signal_field_link_name = serialized["$signal"]
        serialized["$signal"] = serialized[f"&{signal_field_link_name}"][0]
        del serialized[f"&{signal_field_link_name}"]

        return serialized
