"""For parsing the nxdl file into dataclasses, makes the logic of making pydantic
classes of NXDL easier to understand."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from defusedxml import ElementTree as ET


def _xml_tag_without_format_prefix(tag: str) -> str:
    return tag.split("}")[-1]


@dataclass
class ParsedAttribute:
    name: str
    required: bool

    @classmethod
    def from_xml(cls, root: ET.Element[str]) -> ParsedAttribute:
        name = root.get("name")
        required = root.get("optional") == "false"
        if name is None:
            raise ValueError("NX attribute does not have a name.")

        return ParsedAttribute(name, required)


@dataclass
class ParsedField:
    name: str
    type: str | None  # The NX type... we throw this away for now.
    units: str | None  # We don't use this either.
    attributes: list[ParsedAttribute]
    required: bool

    @classmethod
    def from_xml(cls, root: ET.Element[str]) -> ParsedField:
        name = root.get("name")
        type_ = root.get("type")
        units = root.get("units")
        required = root.get("optional") == "false"
        attributes = []
        for sub_element in root.iter():
            for sub_sub_element in sub_element:
                if _xml_tag_without_format_prefix(sub_sub_element.tag) == "attribute":
                    attributes.append(ParsedAttribute.from_xml(sub_sub_element))

        if name is None:
            raise ValueError("NX field does not have name.")
        return ParsedField(
            name=name,
            type=type_,
            units=units,
            attributes=[],
            required=required,
        )


@dataclass
class ParsedSubGroup:
    name_in_parent: str | None
    subgroup_nxdl_file: str
    is_generic: bool
    required: bool


@dataclass
class ParsedGroup:
    name: str
    type: str
    extends: str | None
    sub_groups: dict[str, ParsedSubGroup]
    generic_sub_groups: list[ParsedSubGroup]
    fields: list[ParsedField]
    attributes: list[ParsedAttribute]

    @classmethod
    def from_xml(cls, root: ET.Element[str]) -> ParsedGroup:
        type_: str | None = None

        name = root.get("name")
        if name is None:
            raise ValueError("No NX name on the definition found.")

        type_ = root.get("type")
        if extends := root.get("extends"):
            extends = f"{extends}.nxdl.xml"
        if type_ is None:
            raise ValueError("NX group without a name.")

        attributes = []
        fields = []
        sub_groups = {}
        generic_sub_groups = []

        for sub_element in root:
            if _xml_tag_without_format_prefix(sub_element.tag) == "field":
                fields.append(ParsedField.from_xml(sub_element))
            if _xml_tag_without_format_prefix(sub_element.tag) == "attribute":
                attributes.append(ParsedAttribute.from_xml(sub_element))
            if _xml_tag_without_format_prefix(sub_element.tag) == "group":
                sub_group_type = sub_element.get("type")
                if sub_group_type is None:
                    raise ValueError("No type given in sub group.")

                sub_group_name: str | None = sub_element.get("name")
                sub_group_type = sub_element.get("type")
                sub_group_required = sub_element.get("optional") == "false"

                subgroup_nxdl_file = f"{sub_group_type}.nxdl.xml"
                # Sub groups are generic if they have no name, or if they have any upper case
                # characters, indicating that those characters can be swapped with any name.
                if sub_group_name is None or any(ch.isupper() for ch in sub_group_name):
                    generic_sub_groups.append(
                        ParsedSubGroup(
                            name_in_parent=sub_group_name,
                            subgroup_nxdl_file=subgroup_nxdl_file,
                            is_generic=True,
                            required=sub_group_required,
                        )
                    )
                else:
                    sub_groups[sub_group_name] = ParsedSubGroup(
                        name_in_parent=sub_group_name,
                        subgroup_nxdl_file=subgroup_nxdl_file,
                        is_generic=False,
                        required=sub_group_required,
                    )

        return ParsedGroup(
            name=name,
            type=type_,
            extends=extends,
            sub_groups=sub_groups,
            generic_sub_groups=generic_sub_groups,
            fields=fields,
            attributes=attributes,
        )


def parse_schema_from_nxdl_xml(nxdl_xml: Path) -> ParsedGroup:
    xml_schema = ET.parse(nxdl_xml)
    root = xml_schema.getroot()
    element = None
    for element in root.iter():
        if _xml_tag_without_format_prefix(element.tag) == "definition":
            break
    if element is None:
        raise ValueError("No <definition> found in xml.")
    parsed_schema = ParsedGroup.from_xml(element)

    return parsed_schema
