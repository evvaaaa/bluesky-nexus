"""Tests schema validation on the device layer, without a writer."""

from __future__ import annotations

from pathlib import Path

import pytest
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from bluesky_nexus import NxDevice
from bluesky_nexus.schema import (
    NxAttribute,
    NxBaseClass,
    NxField,
)


@pytest.mark.parametrize(
    ("argument"),
    (
        NxBaseClass.from_path("test_devices/simple_from_yaml_schema.yaml"),
        NxBaseClass.from_path(Path("test_devices") / "simple_from_yaml_schema.yaml"),
        NxBaseClass.from_path(
            Path(__file__).parent.absolute() / "test_devices" / "simple_from_yaml_schema.yaml"
        ),
        NxBaseClass.from_dictionary(
            {
                "$nxclass": "NXsubentry",
                "some_subgroup": {
                    "$nxclass": "NXsubentry",
                    "some_data_key": "some_data_key_value",
                },
                "$some_attribute": "some_attribute_value",
                "another_data_key": "another_data_key_value",
            }
        ),
        NxBaseClass.build("NXsubentry")(
            some_subgroup=NxBaseClass.build("NXsubentry")(
                some_data_key=NxField(data_key="some_data_key_value")
            ),
            some_attribute=NxAttribute(constant="some_attribute_value"),
            another_data_key=NxField(data_key="another_data_key_value"),
        ),
    ),
)
def test_methods_of_loading_schema(argument) -> None:
    class SomeDevice(NxDevice, Device):
        BLUESKY_NEXUS_BASE_CLASS = argument

    assert SomeDevice("X", name="device").hints == {
        "NX_class": "NXsubentry",
        "NX_schema": {
            "$nxclass": "NXsubentry",
            "$some_attribute": "some_attribute_value",
            "some_subgroup": {
                "$nxclass": "NXsubentry",
                "some_data_key": "some_data_key_value",
            },
            "another_data_key": "another_data_key_value",
        },
        "fields": [],
    }


@pytest.mark.parametrize(
    ("data_key_subset"),
    (
        # Full schema definition.
        {"some_alias": {"data_key": "signal"}},
        {"some_alias": "signal"},  # Just the alias.
    ),
)
def test_methods_of_declaring_fields_with_data_keys(data_key_subset: dict) -> None:
    dictionary_schema = {"$nxclass": "NXsubentry"}
    dictionary_schema.update(data_key_subset)

    class SomeDevice(NxDevice, Device):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_dictionary(dictionary_schema)
        signal = Cpt(EpicsSignal, "SIGNAL")

    assert SomeDevice(name="foo").hints == {
        "NX_class": "NXsubentry",
        "NX_schema": {
            "some_alias": "signal",
            "$nxclass": "NXsubentry",
        },
        "fields": [],
    }
