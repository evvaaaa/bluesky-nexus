"""
This module contains the base for all bluesky nexus pydantic schemas, `NxBase`. As well as
their subclasses `NxGroup` and `NxField`.


When `nx_class` is specified in the schema, the correct nexus class is automatically
selected and initialized by `NxBase.from_dictionary`.
This module contains a decorator for appending different instrument schema basemodels to
a global dictionary.
"""

from __future__ import annotations

from abc import ABC
from functools import cached_property
from pprint import pformat
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ConfigDict, computed_field, model_validator

from bluesky_nexus.constants import DEVICE_SCHEMA_NAME_KEY

NX_CLASS_TO_BASEMODEL: dict[str, type[NxBase]] = {}
"""Stores all the allowable nexus_class names and maps them
to the type of nexus basemodel used to validate them."""


def _nexus_class_name_from_python_class(cls: type[NxBase]) -> str:
    python_name = cls.__qualname__

    if not python_name.startswith("Nx"):
        raise ValueError(
            f"Nexus basemodels must start with 'Nx'. This basemodel is called "
            f"'{python_name}'."
        )

    return f"NX{python_name.lstrip('Nx').lower()}"


T = TypeVar("T", bound="NxBase")


class NxBase(BaseModel, ABC):
    """Validates the nexus schema of a device."""

    @computed_field  # type: ignore
    @cached_property
    def nx_class(self) -> str:
        """The nexus baseclass of this group. Uses the python class name,
        e.g NxDevice -> NXdevice.
        """
        return _nexus_class_name_from_python_class(type(self))

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls: type[T], dictionary: dict[str, Any]) -> T:
        """Load a dictionary into a basemodel.

        If an nx_class is specified in the schema and there exists
        a basemodel in the python environment (added through `add_nx_class_basemodel`
        then it will be used.
        """
        return cls._from_dict(dictionary=dictionary)

    @classmethod
    def _from_dict(
        cls: type[T], dictionary: dict[str, Any], parent_key: str | None = None
    ) -> T:
        kwargs: dict[str, Any] = {}
        document_cls: type[NxBase] | None = None

        for key, value in dictionary.items():
            match (key, value):
                # The class is specified. It is fetched from the environment for
                # validation on instantiation:
                case ("nx_class", value):
                    nx_class_name = value
                    maybe_document_cls = NX_CLASS_TO_BASEMODEL.get(nx_class_name)
                    if maybe_document_cls is None:
                        pretty_allowed_classes = pformat(set(NX_CLASS_TO_BASEMODEL))
                        raise TypeError(
                            f"Requested `nx_class: {nx_class_name}` but this isn't "
                            f"defined with pydantic schemas: {pretty_allowed_classes}"
                        )
                    # Add the parent key to the child:
                    # e.g {"data": {nx_class: NXfield, ...}} ->
                    # {"data": {}, {nx_class: NXfield, nx_alias: data, ...}}
                    if value == "NXfield" and not kwargs.get("nx_alias") and parent_key:
                        kwargs["nx_alias"] = parent_key

                    # Differing reference of parent to sub group/field
                    # e.g {"data": {nx_class: NXfield, nx_alias: not_data}}
                    if (
                        value == "NXfield"
                        and (nx_alias := kwargs.get("nx_alias"))
                        and parent_key
                        and nx_alias != parent_key
                    ):
                        pretty_key_value = pformat({parent_key: dictionary})
                        raise TypeError(
                            f"Malformed key, value pair found in nx schema:\n"
                            f"{pretty_key_value}\n"
                            f"`nx_alias: {nx_alias}` is defined explicitely in the "
                            "field but differs from how it's referenced in the parent."
                        )
                    document_cls = maybe_document_cls

                # A subgroup/field is specified:
                # e.g {nx_class: NXobject, SUB_GROUP: {nx_class: NXobject, ...}}
                case (key, value) if isinstance(value, dict):  # A subgroup.
                    kwargs[key] = NxBase._from_dict(value, parent_key=key)  # type: ignore

                # The bluesky datakey with no alias or units:
                # e.g {nx_class: NXobject, <name>-some_data: None}
                case (key, None) if key not in NxField.model_fields:
                    kwargs[key] = NxField(datakey=key)

                # This is one of the other keys in the `NxField`
                case (key, value) if key in NxField.model_fields:
                    kwargs[key] = value

                # A mapping of alias to datakey:
                # e.g {some_alias: <name>-some_datakey}
                case (key, value) if isinstance(key, str) and isinstance(value, str):
                    kwargs[key] = NxField(datakey=value)

                case (key, value) if key not in NxField.model_fields:
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n"
                        f"{pretty_key_value}"
                    )

        if document_cls is None:
            raise TypeError("No `nx_class` specified in a parsed dictionary.")

        return cast(T, document_cls(**kwargs))

    def patch_object_keys(self: T, patched_name: str) -> T:
        """Give a new schema with the name patched to the given one."""
        nx_class = type(self)
        return nx_class.from_dict(
            _patch_string_across_dictionary(
                DEVICE_SCHEMA_NAME_KEY, patched_name, self.model_dump()
            )
        )


def add_nx_class_basemodel(cls: type[T]) -> type[T]:
    """
    Use to wrap a subclass of `NxGroup` so that it can be loaded
    from the literal in any static schema.
    """
    nx_class_name = _nexus_class_name_from_python_class(cls)
    if already_present := NX_CLASS_TO_BASEMODEL.get(nx_class_name):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} cannot be added as an nx_class "
            f"as it's already present as "
            f"{already_present.__module__}.{already_present.__qualname__}"
        )
    NX_CLASS_TO_BASEMODEL[nx_class_name] = cls
    return cls


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


@add_nx_class_basemodel
class NxGroup(NxBase):
    """Validates the nexus schema of a device."""

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


def datakey_to_default_alias(datakey: str) -> str:
    """
    Give the default nx_alias (name of the field in the nexus file
    for a given datakey.
    """
    return (
        datakey.lstrip(DEVICE_SCHEMA_NAME_KEY).lstrip("_").lstrip("-")
        if datakey != DEVICE_SCHEMA_NAME_KEY
        else DEVICE_SCHEMA_NAME_KEY
    )


@add_nx_class_basemodel
class NxField(NxBase):
    """Represents a datakey which corresponds to a nexus field type."""

    datakey: str
    """The bluesky datakey. The '<name>' in this string will be swapped with the
    object name."""

    nx_alias: str = ""
    """The name which is used as the alias. Will default to datakey
    with object name stripped if not provided."""

    nx_units: str | None = None
    """An optional units field. By default the units from the bluesky
    document model will be used, but this can be used to override them
    in the event they aren't specified there.
    """

    @model_validator(mode="before")
    def _set_default_alias(cls, values):
        """Ensure nx_alias defaults to datakey when not provided."""
        if isinstance(values, dict) and not values.get("nx_alias"):
            values["nx_alias"] = datakey_to_default_alias(
                # Default to "" so that we don't get an error on the autogenerated
                # alias, but on the datakey if the datakey isn't provided.
                values.get("datakey", "")
            )
        return values


DISALLOWED_ALIASES_AND_OBJECT_NAMES = frozenset(NxField.model_fields)
