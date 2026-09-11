"""
This module contains the base class for all bluesky nexus pydantic fields and groups: ``NxBase``

This is a common class for any node in the bluesky nexus schema tree, enforcing common
rules between `NxGroup` and `NxField`.
"""

from __future__ import annotations

import re
from abc import ABC
from typing import TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)

from .nx_attribute import NxAttribute

T = TypeVar("T", bound="NxBase")

_ALPHA_NUMERIC_WITH_UNDERSCORES = re.compile(r"^[A-Za-z0-9_]+$")
"""Regex for verifying that keys are only alphanumeric with underscores."""


class NxBase(BaseModel, ABC):
    """The initial abstract base class of any ``NxGroup`` or ``NxField``
    in the device to nexus mapping.

    `NxBase` enforces common logic of these two subclasses."""

    model_config = ConfigDict(extra="allow")

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
                key != "" and not _ALPHA_NUMERIC_WITH_UNDERSCORES.match(key)
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
