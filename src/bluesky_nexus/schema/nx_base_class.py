from __future__ import annotations

import os
from pathlib import Path
from types import EllipsisType
from typing import Any, cast
from weakref import WeakValueDictionary

import nexusformat
import pydantic

from ._nxdl_parser import ParsedField, ParsedGroup, parse_schema_from_nxdl_xml
from .nx_attribute import (
    NxAttribute,
)
from .nx_field import NxField
from .nx_group import NxGroup

BLUESKY_NEXUS_DEFINITIONS_DIRECTORY = Path(
    os.environ.get(
        "BLUESKY_NEXUS_DEFINITIONS_DIRECTORY", Path(nexusformat.__path__[0]) / "definitions"
    )
)
"""The directory where bluesky-nexus should look for base_classes and application definitions from.

This directory should contain separate `applications` and `base_classes` directories, which in
turn contain their flat .nxdl.xml files.
"""


BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY = BLUESKY_NEXUS_DEFINITIONS_DIRECTORY / "base_classes"
"""The directory where bluesky-nexus should allow loading of NXDL through NxBaseClass from.

NXDL in this directory should be flat, and separate from the application definitions.
"""

if (
    not BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY.exists()
    and not BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY.is_dir()
):
    raise ValueError(
        f"{BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY} does not exist or is not a directory."
    )


class _NxBaseClassMeta(type(pydantic.BaseModel)):  # type: ignore
    def __getitem__(self, nxdl_name: str) -> type[NxBaseClass]:
        # Normalize to "<name>.nxdl.xml".
        nxdl_name = f"{nxdl_name.removesuffix('.xml').removesuffix('.nxdl')}.nxdl.xml"

        if nxdl_name in _already_made:
            # Don't make a schema twice.
            return _already_made[nxdl_name]

        nxdl_path = BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY / nxdl_name
        parsed = parse_schema_from_nxdl_xml(nxdl_path)

        pydantic_model = _pydantic_model_from_schema_nxdl(parsed)
        _already_made[nxdl_name] = pydantic_model
        return pydantic_model


class NxBaseClass(NxGroup, metaclass=_NxBaseClassMeta): ...


_already_made: WeakValueDictionary[str, type[NxBaseClass]] = WeakValueDictionary()

# TODO: see comment on generic extras in NXDL below.
# def _get_extras_validator(
#     allowed_extras: tuple[
#         type[NxGroup] | type[NxField] | type[NxAttribute] | type[NxInternalLink], ...
#     ],
# ) -> PydanticDescriptorProxy[ModelValidatorDecoratorInfo]:
#     """Applied to the dynamically generated basemodel to force fields which aren't
#     named in the NXDL to be either, NxField, NxAttribute, NxInternalLink, or one of the
#     generic (ALL_CAPS) subgroups"""
#
#     @pydantic.pydantic.model_validator(mode="after")
#     def _validate_extra_arguments(instance: NxGroup) -> NxGroup:
#         for key, value in instance:
#             if key not in type(instance).model_fields and not isinstance(value, allowed_extras):
#                 raise TypeError(
#                     f"Cannot add instance {key} of type {value} to self, as the NXDL "
#                     f"form only allows additional fields of type {allowed_extras}."
#                 )
#
#         return instance
#
#     return _validate_extra_arguments


def _pydantic_field_from_parsed_field(parsed_field: ParsedField) -> type[NxField]:
    """Make a new field subclass type with the required attributes."""
    if not parsed_field.attributes:
        return NxField  # No extra requirement

    direct_attributes: dict[str, tuple[Any, None | EllipsisType]] = {}
    for parsed_attribute in parsed_field.attributes:
        if parsed_attribute.required:
            direct_attributes[parsed_attribute.name] = (NxAttribute, ...)
        else:
            direct_attributes[parsed_attribute.name] = (NxAttribute | None, None)
    return cast(
        type[NxField],
        pydantic.create_model(
            f"{NxField.__name__}Restricted",
            __config__=pydantic.ConfigDict(extra="allow"),
            __base__=NxField,
            **direct_attributes,  # type: ignore
        ),
    )


def _pydantic_model_from_schema_nxdl(parsed_nxdl: ParsedGroup) -> type[NxBaseClass]:
    if parsed_nxdl.extends:
        try:
            base_class = NxBaseClass[parsed_nxdl.extends]  # type: ignore
        except Exception as exception:
            raise TypeError(
                f"Cannot generate schema for {parsed_nxdl.name} as it inherits from "
                f"{parsed_nxdl.extends} which failed with the above exception."
            ) from exception
    else:
        base_class = cast(type[NxBaseClass], NxGroup)

    direct_attributes: dict[str, tuple[Any, None | EllipsisType]] = {}
    for subgroup_field_name, parsed_sub_group in parsed_nxdl.sub_groups.items():
        try:
            direct_attributes[subgroup_field_name] = (
                NxBaseClass[parsed_sub_group.subgroup_nxdl_file],
                None,
            )
        except Exception as exception:
            raise TypeError(
                f"Cannot generate schema for {parsed_nxdl.name} as it contains a subgroup "
                f"{subgroup_field_name} of type {parsed_sub_group.subgroup_nxdl_file} which "
                "failed with the above exception."
            ) from exception

    for parsed_field in parsed_nxdl.fields:
        pydantic_model = _pydantic_field_from_parsed_field(parsed_field)
        if parsed_field.required:
            direct_attributes[parsed_field.name] = (pydantic_model, ...)
        else:
            direct_attributes[parsed_field.name] = (pydantic_model | None, None)

    for parsed_attribute in parsed_nxdl.attributes:
        if parsed_attribute.required:
            direct_attributes[parsed_attribute.name] = (NxAttribute, ...)
        else:
            direct_attributes[parsed_attribute.name] = (NxAttribute | None, None)

    pydantic_model = pydantic.create_model(
        parsed_nxdl.name.removesuffix(".nxdl.xml"),
        __config__=pydantic.ConfigDict(extra="allow"),
        __base__=base_class,
        **direct_attributes,  # type: ignore
    )

    # TODO: We would like to be able to specify this, but NXDL schema doesn't have a neat heirarchy
    # e.g NXobject has a generic sub group GROUPNAME_log which is itself an NXobject.
    # It would be nicer if NeXus didn't do this...
    # Anyways, for now we'll allow any extra fields which are None, or subclasses of the
    # _ALLOWED_EXTRA types as specified in NxGroup.
    # allowed_generic_subgroups: list[NxGroup] = []
    # for parsed_generic_subgroup in parsed_nxdl.generic_sub_groups:
    #     try:
    #         allowed_generic_subgroups.append(
    #             NxBaseClass[parsed_generic_subgroup.subgroup_nxdl_file]  # type: ignore
    #         )
    #     except Exception as exception:
    #         raise TypeError(
    #             f"Cannot generate schema for {parsed_nxdl.name} as it contains a generic "
    #             f"subgroup of {parsed_generic_subgroup.subgroup_nxdl_file} which failed "
    #             "with the above exception."
    #         ) from exception
    #
    # allowed_extra = _ALLOWED_EXTRA + tuple(allowed_generic_subgroups)  # type: ignore
    # pydantic_model.pydantic.model_validator = _get_extras_validator(allowed_extra)

    return cast(type[NxBaseClass], pydantic_model)
