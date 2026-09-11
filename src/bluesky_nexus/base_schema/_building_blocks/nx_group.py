"""
This module contains the base for all bluesky nexus device types `NxGroup`.

This can be subclassed to define bluesky nexus schema corresponding to nxdl schema:
for example `bluesky_nexus.nexusformat_schema.NxMonochromator`

In serialized schema, a group is specified by the presence or an `$nxclass` key,
which is used to fetch the the correct nexus class for validation automatically
on deserialization in `NxGroup.from_dictionary`.

This module also contains a decorator for appending different instrument schema basemodels to
a global dictionary using `add_nx_class_basemodel`.
"""

from __future__ import annotations

from abc import ABC
from functools import cached_property
from pprint import pformat
from typing import Any, TypeVar, cast

from pydantic import (
    ValidatorFunctionWrapHandler,
    computed_field,
    model_serializer,
    model_validator,
)

from .nx_attribute import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NxAttribute,
    prepend_serialized_prefix_to_nx_attributes,
)
from .nx_base import NxBase
from .nx_base_leaf import NxBaseLeaf
from .nx_field import NxField
from .nx_link import (
    NX_LINK_SERIALIZED_PREFIX,
    NxInternalLink,
    prepend_serialized_prefix_to_nx_internal_links,
)

T = TypeVar("T", bound="NxGroup")

NX_CLASS_TO_BASEMODEL: dict[str, type[NxGroup]] = {}
"""Stores all the allowable nexus NXDL names mapped
to the type of nexus basemodel used to validate them."""


def add_nx_class_basemodel[T: "NxGroup"](cls: type[T]) -> type[T]:
    """
    Used to wrap a subclass of `NxGroup` so that it can be loaded
    from the literal in any serialized static schema.
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
    """Gives the correct NeXus NXDL base class name from a pydantic basemodel name,
    e.g "class NxData(NxObject)" -> "NXdata".
    """

    python_name = cls.__name__

    if not python_name.startswith("Nx"):
        raise ValueError(
            f"Nexus basemodels must start with 'Nx'. This basemodel is called '{python_name}'."
        )

    return f"NX{python_name.removeprefix('Nx').lower()}"


def _nx_class_from_serialized_subgroup[T: "NxGroup"](subgroup: dict, cls: type[T]) -> type[T]:
    """Fetch the pydantic model type from the serialized dictionary with ``"$nxclass"``."""
    if (document_nx_class_name := subgroup.get("$nxclass")) is None:
        raise TypeError(
            f"No {NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass attrbute specified in schema."
        )

    nx_cls = NX_CLASS_TO_BASEMODEL.get(document_nx_class_name)
    if nx_cls is None:
        pretty_allowed_classes = pformat(set(NX_CLASS_TO_BASEMODEL))
        raise TypeError(
            f"Requested `{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass: {document_nx_class_name}` "
            f"but this isn't defined with pydantic schemas: {pretty_allowed_classes}"
        )

    # The class is specified. It is fetched from the environment for
    # validation on instantiation.

    if not issubclass(nx_cls, cls):
        # NxSomeGroup.from_dictionary can only initialize subgroups of NxSomeGroup
        # e.g you can NxGroup.from_dictionary to get an NxObject,
        # but you can't NxMonochromator.from_dictionary to get an NxObject
        raise TypeError(
            f"Found the specified NXclass {nx_cls}, but it cannot be "
            f"initialized from `{cls.__name__}.from_dictionary` as it isn't a subclass "
            "of it."
        )
    return nx_cls


class NxGroup(NxBase, ABC):
    """The abstract base class for any NeXus group."""

    @model_serializer
    def _use_shorthand_and_add_at_key_to_attributes(self) -> dict[str, Any]:
        """Dump the schema with short-hand.

        `foo: NxAttribute(constant="bar")` -> `$foo: "bar"`
        `foo: NxField(data_key="bar")` -> `foo: "bar"`
        `foo: NxAttribute(data_key="bar")` -> `$foo: {data_key: "bar"}`
        `foo: NxField(constant="bar")` -> `foo: {constant: "bar"}`
        """
        shortened = {}
        for key, value in self:
            match value:
                case NxAttribute(
                    constant=constant_value,
                    data_key=None,
                    hints_key=None,
                    timestamps_of_data_key=None,
                ):
                    key = prepend_serialized_prefix_to_nx_attributes(key, value)
                    shortened[key] = constant_value
                case NxAttribute():
                    shortened[prepend_serialized_prefix_to_nx_attributes(key, value)] = value
                case NxInternalLink(link=link):
                    key = prepend_serialized_prefix_to_nx_internal_links(key, value)
                    shortened[key] = link
                case NxField(
                    data_key=data_key, constant=None, hints_key=None, timestamps_of_data_key=None
                ) if value.nx_attributes() == {}:
                    # Shorten a datakey if there aren't additional attributes
                    # to the NxField.
                    shortened[key] = data_key
                case None:
                    # None is only ever used as the default for an optional key across all
                    # the schema. We don't need to serialize and dump this key.
                    continue
                case _:
                    shortened[key] = value

        # Manually add the computed field. Pydantic doesn't seem to support `computed_field`
        # with deserialized without manually adding it.
        shortened.update({f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass": self.nxclass.constant})
        return shortened

    @computed_field  # type: ignore
    @cached_property
    def nxclass(self) -> NxAttribute:
        """
        A computed property for getting the NeXus NXDL class name
        from the python class name.

        This field is serialized and dumped and then used for type
        discrimination in deserialization. It should never be replaced in
        subclasses.

        It's presence forces a nice correspondance between the class names
        in a pydantic schema package and the NXDL it represents, e.g
        `class NxSomeBluesky_NexusGroup(NxObject)` -> `"$nxclass": "NXsomebluesky_nexusgroup"`.
        """
        return NxAttribute(
            constant=_nexus_class_name_from_python_class(self.__class__),
        )

    @classmethod
    def _drop_nxclass(cls, values: T) -> T:
        """This drops the nxclass from the values if it is a dict.

        This is performed after the group class has already been determined
        by the serialized "$nxclass" descriminator, but before the other
        elements have been validated against that class.

        This is called from the ``pre_validation`` model validator so that
        subclasses can't create validators which run before it (easily).
        """
        if isinstance(values, dict):
            values.pop("$nxclass", None)
            values.pop("nxclass", None)
        return values

    @model_validator(mode="wrap")
    @classmethod
    def pre_validation(cls, values: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        """Remove nxclass field (serialized or otherwise) from values passed into
        `NxGroup`s, and then call the other validators, some of which are possibly
        defined in subclasses."""
        values = cls._drop_nxclass(values)
        values = cls._deserialize_from_shorthand_with_nxclass_descriminator(values)
        validated = handler(values)
        return validated

    # TODO:
    # For review -
    # It would be nice to have something like this, where we can see whether links point to
    # defined fields ahead of time. It's very hard to do without creating a global cache of
    # which instance is the parent, for all of the contained NxInternalLinks to reference from.
    # For now we leave this out and force implementations of nexus classes to check themselves.
    # @model_validator(mode="after")
    # def _check_nx_links_reference_real_fields_and_subgroups(self) -> Self:
    #     """Check the initialized `NxInternalLink`s point to elements defined on the device."""
    #
    #     if self.instantiated_inside_group:
    #         # Subgroups can't perform this check since NxInternalLink references
    #         # are relative to the device's top level NxGroup
    #         return self
    #
    #     for name, value in self.all_nx_internal_links().items():
    #         attribute = _deep_getattr(self, *value.link)
    #         if attribute is None:
    #             pretty_key_value = pformat({name: value})
    #             raise TypeError(
    #                 "Malformed link specified, the link does not map "
    #                 f"to a defined field in the schema:\n"
    #                 f"{pretty_key_value}"
    #             )
    #
    #         elif not isinstance(attribute, NxGroup | NxField):
    #             pretty_key_value = pformat({name: value})
    #             raise TypeError(
    #                 "Malformed link specified, the link does not map "
    #                 f"to an NxField or NxGroup, instead :\n"
    #                 f"{pretty_key_value}"
    #             )
    #
    #     return self

    def nx_attributes(self) -> dict[str, NxAttribute]:
        """Gives a dict of the nx attributes defined on this group."""
        attributes = NxBase.nx_attributes(self)
        attributes.update({"nxclass": self.nxclass})
        return attributes

    def sub_nx_groups(self) -> dict[str, NxGroup]:
        """Gives all sub `NxGroup` instances in this group."""
        return {k: v for k, v in self if isinstance(v, NxGroup)}

    def all_nx_fields(self) -> dict[str, NxField]:
        """Gives all `NxField` instances in the the entire group tree
        of this group."""
        fields = self.nx_fields()
        for sub_group in self.sub_nx_groups().values():
            fields.update(sub_group.all_nx_fields())
        return fields

    def nx_internal_links(self) -> dict[str, NxInternalLink]:
        """Gives internal links defined on the group."""
        return {k: v for k, v in self if isinstance(v, NxInternalLink)}

    def all_nx_internal_links(self) -> dict[str, NxInternalLink]:
        """Gives all internal links defined on the group and sub groups."""
        links = self.nx_internal_links()
        for sub_group in self.sub_nx_groups().values():
            links.update(sub_group.all_nx_internal_links())
        return links

    def nx_fields(self) -> dict[str, NxField]:
        """Gives all `NxField` instances in the group (not subgroups)."""
        return {k: v for k, v in self if isinstance(v, NxField)}

    @classmethod
    def _deserialize_from_shorthand_with_nxclass_descriminator(cls, values: Any) -> Any:
        """Deserialize the model from shorthand if it is a serialized dictionary.
        Use the "$nxclass" attribute from the serialized subgroups to find the correct class
        to initialize with.

        This is called from the ``pre_validation`` model validator so that
        subclasses can't create validators which run before it (easily).
        """

        kwargs: dict[str, Any] = {}
        if not isinstance(values, dict):
            return values

        # Fields and attributes may need to be initialized through
        # the basemodel class to support subclasses of NxField/NxAttribute
        # on the basemodel. These are fished out the schema and initialized
        # once we have the nxclass type.
        attributes_to_initialize = {}
        fields_to_initialize = {}

        # Links are not designed to be subclassed, but we initialize them later
        # so we can verify that they link valid fields/subgroups.
        links_to_initialize = {}

        for key, value in values.items():
            match (key, value):
                case (key, value) if isinstance(value, NxBase | NxBaseLeaf):
                    kwargs[key] = value  # No deserialization necessary.
                case (key, value) if isinstance(key, str) and key.startswith(
                    NX_ATTRIBUTE_SERIALIZED_PREFIX
                ):
                    key = key.removeprefix(NX_ATTRIBUTE_SERIALIZED_PREFIX)  # deserialized key
                    # Attribute is stored as a dict. If the field is in the basemodel
                    # it will be initialized from the dict later to support subclasses
                    # Of NxAttribute defined on the NxGroup.
                    attributes_to_initialize[key] = (
                        value if isinstance(value, dict) else {"constant": value}
                    )
                # A link is specified:
                # e.g {
                #   $nxclass: NXobject,
                #   some_field: some-dkey,
                #   sub_group: {$nxclass: NXobject, &some_link: ["some_field"]}
                # }
                case (key, value) if isinstance(key, str) and key.startswith(
                    NX_LINK_SERIALIZED_PREFIX,
                ):
                    key = key.removeprefix(NX_LINK_SERIALIZED_PREFIX)  # deserialized key
                    links_to_initialize[key] = (
                        value if isinstance(value, dict) else {"link": value}
                    )

                # A subgroup is specified:
                # e.g {$nxclass: NXobject, SUB_GROUP: {$nxclass: NXobject, ...}}
                case (key, value) if isinstance(value, dict) and "$nxclass" in value:
                    subgroup_cls = _nx_class_from_serialized_subgroup(value, NxGroup)
                    kwargs[key] = subgroup_cls(**value)  # type: ignore

                # A field is specified:
                # e.g {some_alias: {data_key: some_data_key, $long_name: "Longish name"}}
                case (key, value) if isinstance(value, dict):
                    fields_to_initialize[key] = value

                # A mapping of alias to data_key:
                # e.g {some_alias: some_data_key}
                case (key, value) if isinstance(key, str) and isinstance(value, str):
                    fields_to_initialize[key] = {"data_key": value}

                # No value provided, this field/subgroup is optional in the schema
                # and not provided. We don't need to pass it through.
                case (key, None):
                    continue

                case (key, value):
                    pretty_key_value = pformat({key: value})
                    raise TypeError(
                        f"Malformed key, value pair found in nx schema:\n{pretty_key_value}"
                    )

        for key, value in fields_to_initialize.items():
            if key in cls.model_fields:
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
            if key in cls.model_fields:
                kwargs[key] = value
            else:
                kwargs[key] = NxAttribute(**value)

        for key, value in links_to_initialize.items():
            kwargs[key] = NxInternalLink(**value)

        return kwargs

    @classmethod
    def from_dictionary(cls: type[T], dictionary: dict) -> T:
        """Load the serialized `NXgroup` or subclass of `NXgroup` and initialize with it.

        The "$nxclass" field has to be a subclass of the class calling this method, e.g
        ``NxObject.from_dictionary`` can produce an ``NxData``, but
        ``NxData.from_dictionary`` can not produce an ``NxMonochromator``."""

        document_nx_class = _nx_class_from_serialized_subgroup(dictionary, cls)
        return document_nx_class(**dictionary)

    def __add__(self: T, other: NxGroup) -> T:
        """
        Return a new basemodel of one group and another.

        Leaves of the tree, e.g NxField and NxAttribute are added if they aren't
        already defined in self.

        Subgroups will also be added together if `other`'s
        subgroup is a subclass of `self`'s.
        """

        if not isinstance(self, type(other)):
            return self.model_copy()

        in_progress = self.model_dump()

        for other_key, other_value in other:
            our_value = getattr(self, other_key, None)

            if our_value is None:
                # The key is entirely new, we can add it.
                in_progress[prepend_serialized_prefix_to_nx_attributes(other_key, other_value)] = (
                    other_value.model_dump()
                    if isinstance(other_value, NxBase | NxBaseLeaf)
                    else other_value
                )

            elif isinstance(our_value, NxGroup) and isinstance(other_value, NxGroup):
                # The value may be different, but similar enough that we can try to merge them.
                in_progress[prepend_serialized_prefix_to_nx_attributes(other_key, other_value)] = (
                    our_value + other_value
                ).model_dump()

        return cast(T, type(self).from_dictionary(in_progress))
