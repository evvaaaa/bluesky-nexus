from __future__ import annotations

from pprint import pformat
from typing import Any

from pydantic import (
    BaseModel,
    model_validator,
)


class NxAttribute(BaseModel):
    """An attribute which can be attribted to any field or group.

    An attribute can come from one of three sources.
    * A constant specified in the schema, e.g `constant: "eV"`.
    * A key of the hints of a device, e.g `hints_key: ["md", "description"].
    * A bluesky data_key, e.g `"data_key: some_data_key_on_the_object"
    """

    data_key: str | None = None
    hints_key: list[str] | str | None = None
    constant: Any = None

    @model_validator(mode="before")
    def _check_one_of_the_methods_is_defined(cls, values):
        """Ensure nx_alias defaults to data_key when not provided."""
        data_key = values.get("data_key")
        hints_key = values.get("hints_key")

        constant = values.get("constant")
        provided_count = len(
            [v for v in (data_key, hints_key, constant) if v is not None]
        )
        if provided_count != 1:
            pretty_key_value = pformat(
                {
                    values.get("name"): {
                        "data_key": data_key,
                        "hints_key": hints_key,
                        "constant": constant,
                    }
                }
            )
            raise TypeError(
                f"Malformed attribute found in nx schema. "
                "One method of obtaining the attribte value should be provided:\n"
                f"{pretty_key_value}"
            )
        return values
