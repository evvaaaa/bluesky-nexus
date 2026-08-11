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

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from typing_extensions import Self

NX_CLASS_TO_BASEMODEL: dict[str, type[NxBase]] = {}
"""Stores all the allowable nexus_class names and maps them
to the type of nexus basemodel used to validate them."""


def _nexus_class_name_from_python_class(cls: type[NxBase]) -> str:
    python_name = cls.__name__

    if not python_name.startswith("Nx"):
        raise ValueError(
            f"Nexus basemodels must start with 'Nx'. This basemodel is called "
            f"'{python_name}'."
        )

    return f"NX{python_name.removeprefix('Nx').lower()}"


T = TypeVar("T", bound="NxBase")


class NxBase(BaseModel, ABC):
    """The initial base class of any nx schema in the device to nexus mapping."""

    @computed_field  # type: ignore
    @cached_property
    def nxclass(self) -> str:
        """
        A computed proprty for getting the nexus base class name from
        the python class name.
        """
        return _nexus_class_name_from_python_class(self.__class__)

    model_config = ConfigDict(
        extra="allow",
        alias_generator=lambda n: "@nxclass" if n == "nxclass" else n,
        serialize_by_alias=True,
    )

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> Self:
        """Load a dictionary into a basemodel.

        If an @nxclass is specified in the schema and there exists
        a basemodel in the python environment (added through `add_nx_class_basemodel`
        then it will be used.
        """
        return cls._from_dict(dictionary=dictionary)

    @classmethod
    def _from_dict(
        cls, dictionary: dict[str, Any], parent_key: str | None = None
    ) -> Self:
        kwargs: dict[str, Any] = {}
        document_cls: type[NxBase] | None = None

        for key, value in dictionary.items():
            match (key, value):
                # The class is specified. It is fetched from the environment for
                # validation on instantiation. This is the only attribute which
                # has to be constant.
                case ("@nxclass", value):
                    nx_class_name = value
                    maybe_document_cls = NX_CLASS_TO_BASEMODEL.get(nx_class_name)
                    if maybe_document_cls is None:
                        pretty_allowed_classes = pformat(set(NX_CLASS_TO_BASEMODEL))
                        raise TypeError(
                            f"Requested `@nxclass: {nx_class_name}` but this isn't "
                            f"defined with pydantic schemas: {pretty_allowed_classes}"
                        )
                    # Add the parent key to the child:
                    # e.g {"data": {@nxclass: NXfield, ...}} ->
                    # {"data": {}, {@nxclass: NXfield, nx_alias: data, ...}}
                    if value == "NXfield" and not kwargs.get("nx_alias") and parent_key:
                        kwargs["nx_alias"] = parent_key

                    # Differing reference of parent to sub group/field
                    # e.g {"data": {@nxclass: NXfield, nx_alias: not_data}}
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

                # Attribute specified:
                case (key, value) if isinstance(key, str) and key.startswith("@"):
                    # e.g {@units: mA}
                    if isinstance(value, dict):
                        if (
                            name_contained := value.get("name")
                        ) and name_contained != key:
                            # Differing reference of parent to attribute
                            # e.g {"@units": {name="@something_else}}
                            pretty_key_value = pformat({key: value})
                            raise TypeError(
                                f"Malformed attribute found in nx schema:\n"
                                f"{pretty_key_value}\n"
                                f"`name: {name_contained}` is defined "
                                f"explicitely in the attribute but differs from {key} "
                                "referenced in the parent."
                            )
                        value["name"] = (
                            key  # We've checked it's either not provided or the same
                        )
                        kwargs[key] = NxAttribute(**value)

                    else:
                        kwargs[key] = NxAttribute(name=key, constant=value)

                    # TODO: Check that the value is an acceptable on for
                    # nexus schema and raise this error otherwise.
                    # else:
                    #     pretty_key_value = pformat({key: value})
                    #     raise TypeError(
                    #         f"Malformed attribute found in nx schema:\n"
                    #         f"{pretty_key_value}\n"
                    #     )

                # A subgroup/field is specified:
                # e.g {@nxclass: NXobject, SUB_GROUP: {@nxclass: NXobject, ...}}
                case (key, value) if isinstance(value, dict):  # A subgroup.
                    kwargs[key] = NxBase._from_dict(value, parent_key=key)  # type: ignore

                # No value provided, this field/subgroup was probably specified in
                # the schema but not provided.
                case (key, None) if key not in NxField.model_fields:
                    pass

                # This is one of the other keys in the `NxField`
                case (key, value) if key in NxField.model_fields:
                    kwargs[key] = value

                # A mapping of alias to data_key:
                # e.g {some_alias: some_data_key}
                case (key, value) if isinstance(key, str) and isinstance(value, str):
                    kwargs[key] = NxField(data_key=value, nx_alias=key)

                case (key, value) if key not in NxField.model_fields:
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n"
                        f"{pretty_key_value}"
                    )

        if document_cls is None:
            raise TypeError(
                f"No `@nxclass` specified in a parsed dictionary {pformat(dictionary)}."
            )

        return cast(Self, document_cls(**kwargs))

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this object."""
        return {k: v for k, v in self if isinstance(v, NxAttribute)}

    def __add__(self, other: Self) -> Self:
        """
        Add one group to another, treating the left group
        with priority in the case of conflicts.
        """
        in_progress = self.model_dump()

        for other_key, other_value in other:
            # We only care about nexus attributes
            # (attributes in the python sense).

            our_value = getattr(self, other_key, None)

            # The key is entirely new.
            if our_value is None:
                in_progress[other_key] = (
                    other_value.model_dump()
                    if isinstance(other_value, NxBase | NxAttribute)
                    else other_value
                )

            elif (
                isinstance(our_value, NxGroup) and isinstance(other_value, NxGroup)
            ) or (isinstance(our_value, NxField) and isinstance(other_value, NxField)):
                # The value may be different different,
                # but similar enough that we can try to merge them.
                in_progress[other_key] = (our_value + other_value).model_dump()  # type: ignore

        return type(self).from_dict(in_progress)


class NxAttribute(BaseModel):
    """An attribute which can be attribted to any field or group.

    An attribute can come from one of three sources.
    * A constant specified in the schema, e.g `constant: "eV"`.
    * A key of the hints of a device, e.g `hints_key: ["md", "description"].
    * A bluesky data_key, e.g `"data_key: some_data_key_on_the_object"

    """

    name: str = Field(pattern=r"^@.+$")
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


def add_nx_class_basemodel(cls: type[T]) -> type[T]:
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


@add_nx_class_basemodel
class NxField(NxBase):
    """Represents a data_key which corresponds to a nexus field type.

    If the "@units" NxAttribute is not provided then it will be added
    by the callback using the defintion found in bluesky (if provided).
    """

    data_key: str
    """The bluesky data_key. The '<name>' in this string will be swapped with the
    object name."""

    nx_alias: str = ""
    """The name which is used as the alias. Will default to data_key
    with object name stripped if not provided."""

    @model_validator(mode="before")
    def _set_default_alias(cls, values):
        """Ensure nx_alias defaults to data_key when not provided."""
        if isinstance(values, dict) and not values.get("nx_alias"):
            values["nx_alias"] = values.get("data_key")
        return values


DISALLOWED_ALIASES_AND_OBJECT_NAMES = frozenset(NxField.model_fields)
