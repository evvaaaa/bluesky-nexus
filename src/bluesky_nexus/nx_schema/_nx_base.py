"""
This module contains the base for all bluesky nexus pydantic schemas, `NxBase`.
As well as their subclasses `NxGroup` and `NxField`.


When `@nxclass` is specified in the schema, the correct nexus class is automatically
selected and initialized by `NxBase.from_dictionary`.
This module contains a decorator for appending different instrument schema basemodels to
a global dictionary.
"""

from __future__ import annotations

from abc import ABC
from functools import cached_property
from pprint import pformat
from typing import Any, TypeVar, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    model_serializer,
)

from ._nx_attribute import NxAttribute

NX_CLASS_TO_BASEMODEL: dict[str, type[NxBase]] = {}
"""Stores all the allowable nexus_class names and maps them
to the type of nexus basemodel used to validate them."""


def _nexus_class_name_from_python_class(cls: type[NxBase]) -> str:
    python_name = cls.__name__

    if not python_name.startswith("Nx"):
        raise ValueError(
            f"Nexus basemodels must start with 'Nx'. This basemodel is called '{python_name}'."
        )

    return f"NX{python_name.removeprefix('Nx').lower()}"


T = TypeVar("T", bound="NxBase")


def _prepend_at_key_to_attributes(name: str, value: Any) -> str:
    return f"@{name.removeprefix('@')}" if isinstance(value, NxAttribute) else name


class NxBase(BaseModel, ABC):
    """The initial base class of any nx schema in the device to nexus mapping."""

    model_config = ConfigDict(extra="allow")

    @model_serializer
    def _use_shorthand_and_add_at_key_to_attributes(self) -> dict[str, Any]:
        """Dump the schema with short-hand."""
        shortened = {}
        for key, value in self:
            key = _prepend_at_key_to_attributes(key, value)
            match value:
                case NxAttribute(constant=constant_value, data_key=None, hints_key=None):
                    shortened[key] = constant_value
                case NxField(data_key=data_key) if dict(value).keys() == {"data_key"}:
                    # Shorten a datakey if there arent' additional attributes
                    # to nxclass.
                    shortened[key] = data_key
                case _:
                    shortened[key] = value

        return shortened

    @classmethod
    def from_dictionary(cls, dictionary: dict[str, Any]) -> NxBase:
        """Load a dictionary into a basemodel.

        If an @nxclass is specified in the schema and there exists
        a basemodel in the python environment (added through `add_nx_class_basemodel`
        then it will be used.
        """

        if "@nxclass" in dictionary:
            return NxGroup.from_dictionary(dictionary)
        else:
            return NxField.from_dictionary(dictionary)

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this object."""
        return {k: v for k, v in self if isinstance(v, NxAttribute)}

    def __add__(self: T, other: NxBase) -> T:
        """
        Add one group to another, treating the left group
        with priority in the case of conflicts.

        This is used in heirarchy.
        """
        in_progress = self.model_dump()

        for other_key, other_value in other:
            # We only care about nexus attributes
            # (attributes in the python sense).

            our_value = getattr(self, other_key, None)

            # The key is entirely new.
            if our_value is None:
                in_progress[_prepend_at_key_to_attributes(other_key, other_value)] = (
                    other_value.model_dump()
                    if isinstance(other_value, NxBase | NxAttribute)
                    else other_value
                )

            elif (isinstance(our_value, NxGroup) and isinstance(other_value, NxGroup)) or (
                isinstance(our_value, NxField) and isinstance(other_value, NxField)
            ):
                # The value may be different different,
                # but similar enough that we can try to merge them.
                in_progress[_prepend_at_key_to_attributes(other_key, other_value)] = (
                    our_value + other_value
                ).model_dump()

        return cast(T, type(self).from_dictionary(in_progress))


def add_nx_class_basemodel[T: "NxBase"](cls: type[T]) -> type[T]:
    """
    Use to wrap a subclass of `NxGroup` so that it can be loaded
    from the literal in any static schema.
    """
    nx_class_name = _nexus_class_name_from_python_class(cls)
    if already_present := NX_CLASS_TO_BASEMODEL.get(nx_class_name):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} cannot be added as an @nxclass "
            f"as it's already present as "
            f"{already_present.__module__}.{already_present.__qualname__}"
        )
    NX_CLASS_TO_BASEMODEL[nx_class_name] = cls
    return cls


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
        return {k: v for k, v in self if isinstance(v, NxField)}

    def sub_nx_groups(self) -> dict[str, NxGroup]:
        """Return all `NxGroup`instances in the group."""
        return {k: v for k, v in self if isinstance(v, NxGroup)}

    @computed_field  # type: ignore
    @cached_property
    def nxclass(self) -> NxAttribute:
        """
        A computed proprty for getting the nexus base class
        attribute from the python class name.
        """
        return NxAttribute(
            constant=_nexus_class_name_from_python_class(self.__class__),
        )

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this object."""
        attributes = NxBase.nx_attributes(self)
        attributes.update({"nxclass": self.nxclass})
        return attributes

    @model_serializer
    def _use_shorthand_and_add_at_key_to_attributes(self) -> dict[str, Any]:
        """Dump the schema with short-hand."""
        # Manually add the computed field.

        shortened = NxBase._use_shorthand_and_add_at_key_to_attributes(self)
        shortened.update({"@nxclass": self.nxclass.constant})
        return shortened

    @classmethod
    def from_dictionary(cls: type[T], dictionary: dict) -> T:
        kwargs: dict[str, Any] = {}
        document_nx_class_name: str | None = None

        for key, value in dictionary.items():
            match (key, value):
                # Attribute specified:
                case (key, value) if isinstance(key, str) and key.startswith("@"):
                    attribute = (
                        NxAttribute(**value)
                        if isinstance(value, dict)
                        else NxAttribute(constant=value)
                    )
                    key = key.removeprefix("@")  # deserialized key
                    if key == "nxclass":
                        document_nx_class_name = attribute.constant
                        # Attribute is thrown away. It is used to select
                        # the correct class where it is a computed property.
                    else:
                        kwargs[key] = attribute

                # A subgroup or field is specified:
                # e.g {@nxclass: NXobject, SUB_GROUP: {@nxclass: NXobject, ...}}
                case (key, value) if isinstance(value, dict):
                    kwargs[key] = NxBase.from_dictionary(value)

                # A mapping of alias to data_key:
                # e.g {some_alias: some_data_key}
                case (key, value) if isinstance(key, str) and isinstance(value, str):
                    kwargs[key] = NxField(data_key=value)

                # No value provided, this field/subgroup was probably specified in
                # the schema but not provided.
                case (key, None):
                    continue

                case (key, value):
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n{pretty_key_value}"
                    )

        if document_nx_class_name is None:
            raise TypeError("No @nxclass attrbute specified in nx schema.")

        # The class is specified. It is fetched from the environment for
        # validation on instantiation
        #
        document_cls = NX_CLASS_TO_BASEMODEL.get(document_nx_class_name)
        if document_cls is None:
            pretty_allowed_classes = pformat(set(NX_CLASS_TO_BASEMODEL))
            raise TypeError(
                f"Requested `@nxclass: {document_nx_class_name}` but this isn't "
                f"defined with pydantic schemas: {pretty_allowed_classes}"
            )
        if not issubclass(document_cls, cls):
            raise TypeError(
                f"Found the specified NXclass {document_cls}, but it cannot be "
                f"initialized from `{cls.__name__}.from_dictionary` as it isn't a subclass "
                "of it."
            )
        return cast(T, document_cls(**kwargs))


class NxField(NxBase):
    """Represents a data_key which corresponds to a nexus field type.

    If the "@units" `NxAttribute` is not provided then it will be added
    by the callback using the defintion found in bluesky (if provided).
    """

    data_key: str
    """The bluesky data_key. The '<name>' in this string will be swapped with the
    object name."""

    @classmethod
    def from_dictionary(cls: type[T], dictionary: dict) -> T:
        kwargs = {}
        for key, value in dictionary.items():
            match (key, value):
                # Attribute specified:
                case (key, value) if key.startswith("@"):
                    attribute = (
                        NxAttribute(**value)
                        if isinstance(value, dict)
                        else NxAttribute(constant=value)
                    )
                    kwargs[key.removeprefix("@")] = attribute

                # This is one of the other keys in the `NxField`
                case (key, value) if key in cls.model_fields:
                    kwargs[key] = value

                case (key, value):
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n{pretty_key_value}"
                    )

        return cls(**kwargs)
