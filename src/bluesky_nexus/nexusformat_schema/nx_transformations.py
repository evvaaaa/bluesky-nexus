"""Contains the definition for NXtransformations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import model_validator

from bluesky_nexus.base_schema import (
    NxAttribute,
    NxConstantAttribute,
    NxField,
    add_nx_class_basemodel,
)

from .nx_object import NxObject

_NxTransformationVectorIndex = Literal[0, 1, -1]


class NxTransformationsAxisField(NxField):
    vector: NxConstantAttribute[
        tuple[
            _NxTransformationVectorIndex,
            _NxTransformationVectorIndex,
            _NxTransformationVectorIndex,
        ]
    ]

    depends_on: NxAttribute = NxConstantAttribute(constant=".")
    """Points to the path of a field defining the axis on which this instance of
    NXtransformations depends or the string “.”. It can also point to an instance
    of NX_coordinate_system if this transformation depends on it."""

    """A vector referencing the direction of this transformation with relation
    to the geometry specified in `depends_on`."""

    transformation_type: NxConstantAttribute[Literal["translation", "rotation"]] | None = None
    """Whether this transformation is a rotation, or a translation."""

    offset: NxAttribute | None = None
    """A fixed offset applied before the transformation (three vector components)."""

    offset_units: NxAttribute | None = None
    """The units of `offset`."""

    equipment_component: NxAttribute | None = None
    """An arbitrary identifier of a component of the equipment to which the
    transformation belongs, such as ‘detector_arm’ or ‘detector_module’."""


def _validate_fields(transformations: dict[str, Any]) -> None:
    """Validate that the elements are either NxTransformationsAxisField
    or NxFields referencing NxTransformationsAxisField."""

    for key, value in transformations.items():
        if key.endswith("_end") or key.endswith("_increment_set"):
            referenced_transformation_name = key.removesuffix("_end").removesuffix(
                "_increment_set"
            )
            if referenced_transformation_name not in transformations:
                raise TypeError(
                    f"Field {key} is referencing an AXISNAME {referenced_transformation_name} "
                    "which was not provided in the schema"
                )
        elif not isinstance(value, NxAttribute | NxTransformationsAxisField):
            raise TypeError(
                "`NxTransformations` only allows fields corresponding to AXISNAME, "
                "AXISNAME_end, or AXISNAME_increment_set, or attributes. "
                f"Received key of unknown type: {key}: {value}."
            )


@add_nx_class_basemodel
class NxTransformations(NxObject):
    """Represents a NeXus NXtransformations.

    For each axis, if `depends_on`, the specification for the coordinate system,
    is the default https://manual.nexusformat.org/design.html#the-nexus-coordinate-system
    unless specified otherwise.
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields_into_nx_transformations(
        cls, values: dict[str, NxAttribute | NxField]
    ) -> dict[str, NxAttribute | NxField | NxTransformationsAxisField]:
        """Ensures all fields correspond to AXISNAME, or one of the fields referencing AXISNAME."""

        fields = {}
        for key, value in values.items():
            if (
                isinstance(value, NxAttribute)
                or key.endswith("_end")
                or key.endswith("_increment_set")
            ):
                fields[key] = value
            else:
                fields[key] = NxTransformationsAxisField(**value.model_dump())

        _validate_fields(fields)
        return fields
