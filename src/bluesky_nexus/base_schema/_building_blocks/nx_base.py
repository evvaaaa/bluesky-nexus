"""
This module contains the base class for all bluesky nexus pydantic fields and groups: ``NxBase``

This is a common class for any node in the bluesky nexus schema tree, enforcing common
rules between `NxGroup` and `NxField`.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Self, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)

from .nx_attribute import NxAttribute

T = TypeVar("T", bound="NxBase")

ALPHA_NUMERIC_WITH_UNDERSCORES = re.compile(r"^[A-Za-z0-9_]+$")
"""Regex for verifying that keys are only alphanumeric with underscores."""


class NxBase(BaseModel, ABC):
    """The initial abstract base class of any ``NxGroup`` or ``NxField``
    in the device to nexus mapping.

    `NxBase` enforces common logic of these two subclasses."""

    model_config = ConfigDict(extra="allow")

    @classmethod
    @abstractmethod
    def _allowed_value_types(cls) -> tuple[type | None, ...]:
        """Subclasses must provide a class-level set of allowed element types."""

    @model_validator(mode="after")
    def _verify_type_of_values_permitted_by_subclass(self) -> Self:
        allowed_value_types = self._allowed_value_types()
        allowed_value_types_minus_none = tuple(
            value_type for value_type in allowed_value_types if value_type is not None
        )
        none_allowed = allowed_value_types != allowed_value_types_minus_none
        for key, value in self:
            if key in type(self).model_fields:
                continue
            if none_allowed and value is None:
                continue
            if len(allowed_value_types_minus_none) == 0 or not isinstance(
                value, allowed_value_types_minus_none
            ):
                raise TypeError(
                    f"{key} had type {type(value)} which is not an allowed value type in "
                    f"`{type(self).__name__}` values permitted are {allowed_value_types}."
                )
        return self

    @model_validator(mode="before")
    @classmethod
    def _dont_allow_non_alphanumeric_keys(cls, value: dict | NxBase) -> dict | NxBase:
        if isinstance(value, NxBase):
            # This passes the test by virtue of being
            # unserialized python attributes.
            return value

        for key in value:
            if isinstance(key, tuple):
                raise RuntimeError(value, key)
            if (
                # If key is "" it will be replaced by the object name
                # in the writer.
                key != "" and not ALPHA_NUMERIC_WITH_UNDERSCORES.match(key)
            ):
                raise ValueError(
                    f"Non-alphanumeric attribute key: {key!r}. "
                    "Attribute names must be alphanumeric (A-Z, a-z, 0-9) "
                    "and may include underscores."
                )
        return value

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this NxBase."""
        return {k: v for k, v in self if isinstance(v, NxAttribute)}
