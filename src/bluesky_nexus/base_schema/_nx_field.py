"""Contains the basemodel for ``NxField``.

An ``NxField`` is a leaf in the bluesky nexus schema which is data relevant
to a group.
"""

from typing import Any

from pydantic import model_serializer, model_validator

from ._nx_attribute import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NxAttribute,
    prepend_serialized_prefix_to_nx_attributes,
)
from ._nx_base import NxBase
from ._nx_base_leaf import NxBaseLeaf


class NxField(NxBase, NxBaseLeaf):
    """Contains one of a several keys for defining where the data comes from
    through bluesky, as well as possible attributes.

    Also inherits NxBase for serialization, deserialization logic.

    For any NxField in the schema, if the "@units" `NxAttribute` is not
    provided then it will be added by the callback using the defintion
    found in bluesky (if provided).
    """

    @model_validator(mode="before")
    @classmethod
    def _coerce_attribute(cls, values: Any) -> Any:
        """Coerces attribute when they're deserialized.

        Allows for subclasses to validate against members which may themselves be subclasses of
        NxAttribute/NxField"""

        if not isinstance(values, dict):
            return values

        coerced_attributes: dict[str, NxField | NxAttribute | dict] = {}
        for key, value in values.items():
            if key.startswith(NX_ATTRIBUTE_SERIALIZED_PREFIX):
                key = key.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)
                # NxAttribute have the shorthand where a `$field: value` is
                # `$field: {constant: value}`.
                value = value if isinstance(value, dict) else {"constant": value}
                if key in cls.model_fields:
                    # Allow the model to validate against possible subclasses of
                    # NxAttribute.
                    coerced_attributes[key] = value
                else:
                    # The nx attribute isn't specified in schema. Add it.
                    coerced_attributes[key] = NxAttribute(**value)

            else:
                coerced_attributes[key] = value

        return coerced_attributes

    @model_serializer
    def _use_shorthand_and_add_at_key_to_attributes(self) -> dict[str, Any]:
        """Dump the schema with short-hand.

        * `foo: NxAttribute(constant="bar")` -> `$foo: "bar"`
        * `foo: NxField(data_key="bar")` -> `foo: "bar"`
        * `foo: NxField(data_key="bar", some_attribute=NxAttribute(constant=1))`
              -> `foo: {"data_key": "bar", $some_attribute: 1}`
        * `foo: NxField(constant="bar")` -> `foo: {"constant": "bar"}`"""
        shortened = {}
        for key, value in self:
            key = prepend_serialized_prefix_to_nx_attributes(key, value)
            match value:
                case NxAttribute(constant=constant_value, data_key=None, hints_key=None):
                    shortened[key] = constant_value
                case None if key in NxBaseLeaf.model_fields:
                    continue  # Value is `None` for unused field.
                case _:
                    shortened[key] = value

        return shortened
