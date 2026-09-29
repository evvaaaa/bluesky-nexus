"""Tests schema validation on the device layer, without a writer."""

from __future__ import annotations

from pathlib import Path

import pytest
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd.sim import SynAxis
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.sim import SimPointDetector

from bluesky_nexus import NxDevice
from bluesky_nexus.schema import (
    BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY,
    NxAttribute,
    NxBaseClass,
    NxField,
    NxGroup,
)
from bluesky_nexus.schema._nx_base import NxBase


def test_methods_of_loading_schema() -> None:
    def check_hints(cls):
        assert cls("X", name="device").hints == {
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

    class SomeDevice(
        NxDevice[NxBaseClass.from_path("test_devices/simple_from_yaml_schema.yaml")], Device
    ): ...

    check_hints(SomeDevice)

    class SomeDevice(
        NxDevice[NxBaseClass.from_path(Path("test_devices") / "simple_from_yaml_schema.yaml")],
        Device,
    ): ...

    check_hints(SomeDevice)

    class SomeDevice(
        NxDevice[
            NxBaseClass.from_path(
                (
                    Path(__file__).parent.absolute()
                    / "test_devices"
                    / "simple_from_yaml_schema.yaml"
                )
            )
        ],
        Device,
    ): ...

    check_hints(SomeDevice)

    class SomeDevice(
        NxDevice[
            NxBaseClass["NXsubentry"](
                **{
                    "some_subgroup": {
                        "$nxclass": "NXsubentry",
                        "some_data_key": "some_data_key_value",
                    },
                    "$some_attribute": "some_attribute_value",
                    "another_data_key": "another_data_key_value",
                }
            )
        ],
        Device,
    ): ...

    check_hints(SomeDevice)

    class SomeDevice(
        NxDevice[
            NxBaseClass["NXsubentry"](
                some_subgroup=NxBaseClass["NXsubentry"](
                    some_data_key=NxField(data_key="some_data_key_value")
                ),
                some_attribute=NxAttribute(constant="some_attribute_value"),
                another_data_key=NxField(data_key="another_data_key_value"),
            )
        ],
        Device,
    ): ...

    check_hints(SomeDevice)


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

    class SomeDevice(NxDevice[NxBaseClass.from_dictionary(dictionary_schema)], Device):
        signal = Cpt(EpicsSignal, "SIGNAL")

    assert SomeDevice(name="foo").hints == {
        "NX_class": "NXsubentry",
        "NX_schema": {
            "some_alias": "signal",
            "$nxclass": "NXsubentry",
        },
        "fields": [],
    }
