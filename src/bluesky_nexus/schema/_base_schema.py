"""
This module contains the NxBase class, which has the most basic validation on the
structure all device schema must correspond to of the schema.


When nx_instrument is specified in the schema, the correct nexus class is automatically
selected and initialized by `NxBase.from_dictionary`.
This module contains a decorator for appending different instrument schema basemodels to
a global dictionary.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from bluesky_nexus.common.logging_utils import logger


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


class NxField(BaseModel):
    """Represents a datakey which corresponds to a nexus field type."""

    datakey: str
    """The bluesky datakey the name of the device should be swapped with <obj>."""

    nx_alias: str | None = None
    """An optional alias."""

    nx_units: str | None = None
    """An optional units field. By default the units from the bluesky
    document model will be used, but this can be used to override them
    in the event they aren't specified there.
    """


T = TypeVar("T", bound="NxBase")

DISALLOWED_ALIASES_AND_OBJECT_NAMES = frozenset(
    ["nx_class", "nx_alias", "datakey", "nx_class", "nx_instrument"]
)
"""Datakeys from bluesky will be skipped if they have this name."""

_DIRECT_ADDITION_FIELDS = frozenset(["nx_class"])
"""Fields which should be directly added as key value."""


class NxBase(BaseModel):
    """Validates the nexus schema of a device.

    If `nx_instrument` is specified it will use the instrument of the same
    name in this class. Otherwise it will not do any validation other than
    check that the dictionary will be parsable by the callback.
    """

    nx_class: str = Field("NXobject")
    """The nexus baseclass of this group."""

    model_config = ConfigDict(extra="allow")

    def all_nx_fields(self) -> frozenset[NxField]:
        """Return all `NxField` instances in the group and subgroup."""
        datakeys: list[NxField] = []
        for value in self.__dict__.values():
            if isinstance(value, NxField):
                datakeys.append(value)
            elif isinstance(value, NxBase):
                # recurse into nested NxBase instances
                datakeys.extend(value.all_nx_fields())
        return frozenset(datakeys)

    def nx_fields(self) -> frozenset[NxField]:
        """Return all `NxField` instances in the group (not subgroups)."""
        return frozenset(
            [value for value in self.__dict__.values() if isinstance(value, NxField)]
        )

    def sub_nx_groups(self) -> frozenset[NxBase]:
        """Return all `NxBase`instances in the group."""
        return frozenset(
            [value for value in self.__dict__.values() if isinstance(value, NxBase)]
        )

    @classmethod
    def from_dict(cls: type[T], dictionary: dict[str, Any]) -> T:
        """Load a dictionary into a basemodel."""
        kwargs = {}
        document_cls: type[NxBase] = cls

        for key, value in dictionary.items():
            if key == "nx_instrument":
                nx_instrument = value
                maybe_document_cls = _nx_instrument_to_pydantic_model.get(nx_instrument)
                if maybe_document_cls is None:
                    raise TypeError(
                        f"Requested `nx_instrument: {nx_instrument}` but this isn't "
                        "defined to have a pydantic schema. Remove this key to only "
                        "use primative validation."
                    )
                document_cls = maybe_document_cls
            elif value is None:
                kwargs[key] = NxField(datakey=key)
            elif isinstance(value, dict) and (nx_alias := value.get("nx_alias")):
                kwargs[key] = NxField(datakey=key, nx_alias=nx_alias)
            elif isinstance(value, dict):
                kwargs[key] = NxBase.from_dict(value)
            elif key in _DIRECT_ADDITION_FIELDS:
                kwargs[key] = value
            else:
                logger.warning("Unknown key found in dictionary {}")

        return document_cls(**kwargs)  # type: ignore

    def patch_object_keys(self: T, patched_name: str) -> T:
        """Gives a new schema with the name patched to the given one."""
        nx_class = type(self)
        return nx_class.from_dict(
            _patch_string_across_dictionary("<obj>", patched_name, self.model_dump())
        )


_nx_instrument_to_pydantic_model: dict[str, type[NxBase]] = {}


def add_as_instrument_class(cls: type[T]) -> type[T]:
    instrument_name = cls.__qualname__
    if already_present := _nx_instrument_to_pydantic_model.get(instrument_name):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} cannot be added as an instrument "
            "as it's already present as "
            f"{already_present.__module__}.{already_present.__qualname__}"
        )
    _nx_instrument_to_pydantic_model[instrument_name] = cls
    return cls
