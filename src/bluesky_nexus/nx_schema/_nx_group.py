"""
This module contains the base for all bluesky nexus device types `NxGroup`.

This can be subclassed to define bluesky nexus schema corresponding to nxdl schema:
for example `bluesky_nexus.nx_nexusformat_schema.NxMonochromator`

In serialized schema, a group specified an `$nxclass` key, which
is used to fetch the the correct nexus class for validation automatically on deserialization in
`NxGroup.from_dictionary`.

This module also contains a decorator for appending different instrument schema basemodels to
a global dictionary using `add_nx_class_basemodel`.
"""

from __future__ import annotations

from abc import ABC
from functools import cached_property
from pprint import pformat
from typing import Any, TypeVar, cast

from pydantic import (
    computed_field,
    model_serializer,
)

from bluesky_nexus.nx_schema._nx_base_leaf import NxBaseLeaf

from ._nx_attribute import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NxAttribute,
    prepend_serialized_prefix_to_nx_attributes,
)
from ._nx_base import NxBase
from ._nx_field import NxField

T = TypeVar("T", bound="NxGroup")

NX_CLASS_TO_BASEMODEL: dict[str, type[NxGroup]] = {}
"""Stores all the allowable nexus_class names and maps them
to the type of nexus basemodel used to validate them."""


def add_nx_class_basemodel[T: "NxGroup"](cls: type[T]) -> type[T]:
    """
    Used to wrap a subclass of `NxGroup` so that it can be loaded
    from the literal in any static schema.
    """
    nx_class_name = _nexus_class_name_from_python_class(cls)
    if already_present := NX_CLASS_TO_BASEMODEL.get(nx_class_name):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} cannot be added as an "
            "nxclass as it's already present as "
            f"{already_present.__module__}.{already_present.__qualname__}"
        )
    NX_CLASS_TO_BASEMODEL[nx_class_name] = cls
    return cls


def _nexus_class_name_from_python_class(cls: type[NxGroup]) -> str:
    """Gives the correct nexus format base class name from a pydantic basemodel name,
    e.g "NxData" -> "NXdata".
    """

    python_name = cls.__name__

    if not python_name.startswith("Nx"):
        raise ValueError(
            f"Nexus basemodels must start with 'Nx'. This basemodel is called '{python_name}'."
        )

    return f"NX{python_name.removeprefix('Nx').lower()}"


class NxGroup(NxBase, ABC):
    """Validates the nexus schema of a device."""

    @model_serializer
    def _use_shorthand_and_add_at_key_to_attributes(self) -> dict[str, Any]:
        """Dump the schema with short-hand.

        `foo: NxAttribute(constant="bar")` -> $foo: "bar"`
        `foo: NxField(data_key="bar")` -> foo: "bar"`
        """
        shortened = {}
        for key, value in self:
            key = prepend_serialized_prefix_to_nx_attributes(key, value)
            match value:
                case NxAttribute(constant=constant_value, data_key=None, hints_key=None):
                    shortened[key] = constant_value
                case NxField(data_key=data_key, constant=None, hints_key=None) if (
                    value.nx_attributes() == {}
                ):
                    # Shorten a datakey if there arent' additional attributes
                    # to the NxField.
                    shortened[key] = data_key
                case None:
                    continue  # None is only ever used as the default for an optional key.
                case _:
                    if isinstance(value, NxGroup):
                        shortened[key] = value
                    else:
                        shortened[key] = value

        # Manually add the computed field. Pydantic doesn't seem to support `computed_field`
        # with deserialized without manually adding it.
        shortened.update({f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass": self.nxclass.constant})
        return shortened

    @computed_field  # type: ignore
    @cached_property
    def nxclass(self) -> NxAttribute:
        """
        A computed property for getting the nexus base class
        attribute from the python class name.

        This field is serialized and dumped and then used for type
        discrimination in deserialization.
        """
        return NxAttribute(
            constant=_nexus_class_name_from_python_class(self.__class__),
        )

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this object."""
        attributes = NxBase.nx_attributes(self)
        attributes.update({"nxclass": self.nxclass})
        return attributes

    def sub_nx_groups(self) -> dict[str, NxGroup]:
        """Return all `NxGroup` instances in the group."""
        return {k: v for k, v in self if isinstance(v, NxGroup)}

    def all_nx_fields(self) -> dict[str, NxField]:
        """Return all `NxField` instances in the group and subgroup."""
        fields = self.nx_fields()
        for sub_group in self.sub_nx_groups().values():
            fields.update(sub_group.all_nx_fields())
        return fields

    def nx_fields(self) -> dict[str, NxField]:
        """Return all `NxField` instances in the group (not subgroups)."""
        return {k: v for k, v in self if isinstance(v, NxField)}

    @classmethod
    def from_dictionary(cls: type[T], dictionary: dict) -> T:
        """Load the serialized `NXgroup` or subclass of `NXgroup`."""
        kwargs: dict[str, Any] = {}
        document_nx_class_name: str | None = None

        # Fields and attributes may need to be initialized through
        # the basemodel class to support subclasses of NxField/NxAttribute
        # on the basemodel. These are fished out the schema and initialized
        # once we have the nxclass type.
        attributes_to_initialize = {}
        fields_to_initialize = {}

        for key, value in dictionary.items():
            match (key, value):
                # Attribute specified:
                case (key, value) if isinstance(key, str) and key.startswith(
                    NX_ATTRIBUTE_SERIALIZED_PREFIX
                ):
                    key = key.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)  # deserialized key
                    if key == "nxclass":
                        # Attribute is thrown away. It is used to select
                        # the correct class where it is a computed property.
                        document_nx_class_name = (
                            value.get("constant") if isinstance(value, dict) else value
                        )
                    else:
                        # Attribute is stored as a dict. If the field is in the basemodel
                        # it will be initialized from the dict later to support subclasses
                        # Of NxAttribute defined on the NxGroup.
                        attributes_to_initialize[key] = (
                            value if isinstance(value, dict) else {"constant": value}
                        )

                # A subgroup is specified:
                # e.g {$nxclass: NXobject, SUB_GROUP: {$nxclass: NXobject, ...}}
                case (key, value) if isinstance(value, dict) and "$nxclass" in value:
                    kwargs[key] = NxGroup.from_dictionary(value)

                # A field is specified:
                # e.g {some_alias: {data_key: some_data_key, $long_name: "Longish name"}}
                case (key, value) if isinstance(value, dict):
                    fields_to_initialize[key] = value

                # A mapping of alias to data_key:
                # e.g {some_alias: some_data_key}
                case (key, value) if isinstance(key, str) and isinstance(value, str):
                    fields_to_initialize[key] = {"data_key": value}

                # No value provided, this field/subgroup is optional in the schema
                # and not provided.
                case (key, None):
                    continue

                case (key, value):
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n{pretty_key_value}"
                    )

        if document_nx_class_name is None:
            raise TypeError(
                f"No {NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass attrbute specified in nx schema."
            )

        # The class is specified. It is fetched from the environment for
        # validation on instantiation
        nx_cls = NX_CLASS_TO_BASEMODEL.get(document_nx_class_name)
        if nx_cls is None:
            pretty_allowed_classes = pformat(set(NX_CLASS_TO_BASEMODEL))
            raise TypeError(
                f"Requested `{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass: {document_nx_class_name}` "
                f"but this isn't defined with pydantic schemas: {pretty_allowed_classes}"
            )
        if not issubclass(nx_cls, cls):
            raise TypeError(
                f"Found the specified NXclass {nx_cls}, but it cannot be "
                f"initialized from `{cls.__name__}.from_dictionary` as it isn't a subclass "
                "of it."
            )

        for key, value in fields_to_initialize.items():
            if key in nx_cls.model_fields:
                # Use the raw dictionary. This means
                # that pydantic can infer the possible subclass of
                # NxField from the `nx_cls` and make a new instance
                # of that type.
                kwargs[key] = value
            else:
                # This field isn't specified in the basemodel schema. Just add it
                # as a default NxField.
                kwargs[key] = NxField(**value)

        for key, value in attributes_to_initialize.items():
            # Same logic as the above but with NxAttributes.
            if key in nx_cls.model_fields:
                kwargs[key] = value
            else:
                kwargs[key] = NxAttribute(**value)

        return cast(T, nx_cls(**kwargs))

    def __add__(self: T, other: NxGroup) -> T:
        """
        Return a new basemodel of one group and another.

        Leaves, e.g NxField and NxAttribute are added if they aren't
        already defined in self.

        Subgroups will also be added together if `other`'s
        subgroup is a subclass of `self`'s.
        """

        if not isinstance(self, type(other)):
            return self.model_copy()

        in_progress = self.model_dump()

        for other_key, other_value in other:
            # We only care about nexus attributes
            # (attributes in the python sense).

            our_value = getattr(self, other_key, None)

            if our_value is None:
                # The key is entirely new, we can add it.
                in_progress[prepend_serialized_prefix_to_nx_attributes(other_key, other_value)] = (
                    other_value.model_dump()
                    if isinstance(other_value, NxBase | NxBaseLeaf)
                    else other_value
                )

            elif isinstance(our_value, NxGroup) and isinstance(other_value, NxGroup):
                # The value may be different different,
                # but similar enough that we can try to merge them.
                in_progress[prepend_serialized_prefix_to_nx_attributes(other_key, other_value)] = (
                    our_value + other_value
                ).model_dump()

        return cast(T, type(self).from_dictionary(in_progress))
