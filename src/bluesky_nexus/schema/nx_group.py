"""
This module contains the NxGroup class, which has the most basic validation on the
structure all device schema must correspond to of the schema.


When nx_class is specified in the schema, the correct nexus class is automatically
selected and initialized by `NxGroup.from_dictionary`.
This module contains a decorator for appending different instrument schema basemodels to
a global dictionary.
"""

from __future__ import annotations

from pprint import pformat
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.constants import DEVICE_SCHEMA_NAME_KEY

from .nx_field import NxField


def _patch_string_across_dictionary(
    string_from: str, string_to: str, unpatched_dictionary: dict
) -> dict:
    """To replace string_from with a given string_to across a
    dictionary (keys and values).
    """
    patched_schema = {}
    for key, value in unpatched_dictionary.items():
        if isinstance(value, dict):
            value = _patch_string_across_dictionary(string_from, string_to, value)
        if isinstance(value, str):
            value = value.replace(string_from, string_to)
        if isinstance(key, str):
            key = key.replace(string_from, string_to)

        patched_schema[key] = value

    return patched_schema


T = TypeVar("T", bound="NxGroup")

DISALLOWED_ALIASES_AND_OBJECT_NAMES = frozenset(["nx_class", "nx_alias", "datakey"])
"""Datakeys from bluesky will be skipped if they have this name."""


def datakey_to_default_alias(datakey: str) -> str:
    """
    Give the default nx_alias (name of the field in the nexus file
    for a given datakey.
    """
    return datakey.lstrip(DEVICE_SCHEMA_NAME_KEY).lstrip("_").lstrip("-")


class NxGroup(BaseModel):
    """Validates the nexus schema of a device."""

    nx_class: str = Field("NXobject")
    """The nexus baseclass of this group."""

    model_config = ConfigDict(extra="allow")

    def all_nx_fields(self) -> dict[str, NxField]:
        """Return all `NxField` instances in the group and subgroup."""
        fields = self.nx_fields()
        for sub_group in self.sub_nx_groups().values():
            fields.update(sub_group.all_nx_fields())
        return fields

    def nx_fields(self) -> dict[str, NxField]:
        """Return all `NxField` instances in the group (not subgroups)."""
        nx_fields = {}
        for k in self.model_dump():
            attribute = getattr(self, k)
            if isinstance(attribute, NxField):
                nx_fields[k] = attribute
        return nx_fields

    def sub_nx_groups(self) -> dict[str, NxGroup]:
        """Return all `NxGroup`instances in the group."""
        sub_nx_groups = {}
        for k in self.model_dump():
            attribute = getattr(self, k)
            if isinstance(attribute, NxGroup):
                sub_nx_groups[k] = attribute
        return sub_nx_groups

    @classmethod
    def from_dict(cls: type[T], dictionary: dict[str, Any]) -> T:
        """Load a dictionary into a basemodel.

        If an nx_class is specified in the schema and there exists
        a basemodel in the python environment (added through `add_nx_class_basemodel`
        then it will be used.
        """
        kwargs = {}
        document_cls: type[NxGroup] = cls

        for key, value in dictionary.items():
            match (key, value):
                case ("nx_class", value):
                    nx_class_name = value
                    maybe_document_cls = NX_CLASS_TO_BASEMODEL.get(nx_class_name)
                    if maybe_document_cls is None:
                        raise TypeError(
                            f"Requested `nx_class: {nx_class_name}` but this "
                            "isn't defined with pydantic schema. Change this key to "
                            "an existing class: "
                            f"{pformat(list(NX_CLASS_TO_BASEMODEL))}"
                        )
                    document_cls = maybe_document_cls
                case (key, value) if not value:  # The datakey with no alias or units.
                    kwargs[key] = NxField(
                        datakey=key, nx_alias=datakey_to_default_alias(key)
                    )
                case (key, value) if isinstance(value, dict) and any(
                    nx_data_field_name in value
                    for nx_data_field_name in NxField.model_fields
                ):  # The datakey with some extra nx_field info.
                    if "datakey" not in value:
                        value["datakey"] = key
                    if "nx_alias" not in value:
                        value["nx_alias"] = datakey_to_default_alias(key)
                    kwargs[key] = NxField(**value)
                case (key, value) if isinstance(value, dict):  # A subgroup.
                    kwargs[key] = NxGroup.from_dict(value)  # type: ignore
                case _:
                    pretty_key_value = pformat({key: value})
                    logger.warning(
                        f"Malformed key, value pair found in nx schema: "
                        f"{pretty_key_value}"
                    )

        return document_cls(**kwargs)  # type: ignore

    def patch_object_keys(self: T, patched_name: str) -> T:
        """Give a new schema with the name patched to the given one."""
        nx_class = type(self)
        return nx_class.from_dict(
            _patch_string_across_dictionary(
                DEVICE_SCHEMA_NAME_KEY, patched_name, self.model_dump()
            )
        )


NX_CLASS_TO_BASEMODEL: dict[str, type[NxGroup]] = {}


def add_nx_class_basemodel(cls: type[T]) -> type[T]:
    """
    Use to wrap a subclass of `NxGroup` so that it can be loaded
    from the literal in any static schema.
    """
    nx_class_name = cls.__qualname__
    if already_present := NX_CLASS_TO_BASEMODEL.get(nx_class_name):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} cannot be added as an nx_class "
            "as it's already present as "
            f"{already_present.__module__}.{already_present.__qualname__}"
        )
    NX_CLASS_TO_BASEMODEL[nx_class_name] = cls
    return cls
