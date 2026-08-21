"""Contains `NxBaseLeaf`, an abstract class for enforcing  common rules/allowed elements
in leaves (`NxField` and `NxAttribute`) in the bluesky nexus schema tree.
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
        * A constant specified in the schema, e.g `constant: "eV"`.
        * A key of the hints of a device, e.g `hints_key: ["md", "description"].
        * A bluesky data_key, e.g `"data_key: some_data_key_on_the_object"
        * The timestamps of a bluesky datakey.
    """

    data_key: str | None = None
    timestamps_of_datakey: str | None = None
    hints_key: list[str] | str | None = None
    constant: Any = None

    @model_validator(mode="before")
    @classmethod
    def _check_only_one_of_the_methods_is_defined(
        cls, values: dict | NxBaseLeaf
    ) -> dict | NxBaseLeaf:
        if isinstance(values, dict):
            data_key = values.get("data_key")
            hints_key = values.get("hints_key")
            constant = values.get("constant")
            data_key_timestamps = values.get("timestamps_of_datakey")
        else:
            data_key = getattr(values, "data_key", None)
            hints_key = getattr(values, "hints_key", None)
            constant = getattr(values, "constant", None)
            data_key_timestamps = getattr(values, "data_key", None)

        provided_count = len(
            [v for v in (data_key, hints_key, constant, data_key_timestamps) if v is not None]
        )
        if provided_count != 1:
            pretty_key_value = pformat(values)
            raise TypeError(
                f"Malformed attribute/field found in nx schema. "
                "One method of obtaining the attribute value should be provided:\n"
                f"{pretty_key_value}\n"
            )
        return values

    @model_serializer()
    def _dont_include_unused_optionals_in_serialized_dict(self) -> dict:
        """Serialize only the provided method key (data_key, hints_key, or constant)."""

        serialized_without_unused = {}
        for k, v in self:
            if k in NxBaseLeaf.model_fields:
                if v is not None:
                    serialized_without_unused[k] = v
            else:
                serialized_without_unused[k] = v

        return serialized_without_unused
