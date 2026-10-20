"""Contains ``NxBaseLeaf``, an abstract class for enforcing common rules and
allowed elements in leaves of an ``NxGroup`` - ``NxField`` and ``NxAttribute``.
"""

from __future__ import annotations

from abc import ABC
from pprint import pformat
from typing import Any

from pydantic import BaseModel, model_serializer, model_validator


class NxBaseLeaf(BaseModel, ABC):
    """A leaf in the bluesky nexus schema, either an attribute or
    field.

    It's value can come from one of these sources:
        * A constant specified in the schema, e.g ``constant: "eV"``.
        * A key of the hints of a device, e.g `hints_key: ["md", "description"].
        * A bluesky data_key, e.g ``"data_key": "some_data_key_on_the_object"``
        * The timestamps of a bluesky datakey,
            e.g ``"timestamps_of_data_key": "some_data_key_on_the_object"``
    """

    data_key: str | None = None
    timestamps_of_data_key: str | None = None
    hints_key: list[str] | str | None = None
    constant: Any = None

    @model_validator(mode="before")
    @classmethod
    def _check_only_one_of_the_methods_is_defined(
        cls, values: dict | NxBaseLeaf
    ) -> dict | NxBaseLeaf:
        if isinstance(values, dict):
            defined_sources = {name: values.get(name) for name in NxBaseLeaf.model_fields}
        else:
            defined_sources = {
                name: getattr(values, name, None) for name in NxBaseLeaf.model_fields
            }

        if len([v for v in defined_sources.values() if v is not None]) != 1:
            pretty_key_value = pformat(values)
            raise TypeError(
                f"Malformed attribute/field found in nx schema. "
                "One method of obtaining the attribute value should be provided:\n"
                f"{pretty_key_value}\n"
            )
        return values

    @model_serializer()
    def _dont_include_unused_optionals_in_serialized_dict(self) -> dict:
        """Serialize only the provided method key, and defined values."""

        serialized_without_unused = {}
        for k, v in self:
            if k in NxBaseLeaf.model_fields:
                if v is not None:
                    serialized_without_unused[k] = v
            else:
                serialized_without_unused[k] = v

        return serialized_without_unused
