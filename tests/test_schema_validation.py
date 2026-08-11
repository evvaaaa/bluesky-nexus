"""Tests schema validation on the device layer, without a writer."""

import pytest
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd.sim import SynAxis
from ophyd_async.sim import SimPointDetector
from pydantic import ValidationError

from bluesky_nexus import NexusDevice
from bluesky_nexus.nx_schema.nx_base import NxBase


@pytest.mark.parametrize(
    ("data_key_subset", "expected_alias"),
    (
        # Full schema definition.
        (
            {"some_alias": {"nx_class": "NXfield", "data_key": "signal"}},
            "some_alias",
        ),
        # Just the alias.
        ({"some_alias": "signal"}, "some_alias"),
    ),
)
def test_methods_of_declaring_data_keys(data_key_subset: dict, expected_alias: str):
    dictionary_schema = {"nx_class": "NXobject"}
    dictionary_schema.update(data_key_subset)

    @NexusDevice.from_dictionary(dictionary_schema)
    class SomeDevice(Device):
        signal = Cpt(EpicsSignal, "SIGNAL")

    assert SomeDevice(name="foo").hints == {
        "NX_class": "NXobject",
        "NX_schema": {
            expected_alias: {
                "data_key": "signal",
                "nx_alias": expected_alias,
                "nx_class": "NXfield",
            },
            "nx_class": "NXobject",
        },
        "fields": [],
    }


def test_writer_behaviour_with_failing_schema_specified_in_yaml():
    with pytest.raises(
        ValidationError,
        match=("Input should be a valid dictionary or instance of NxField"),
    ):

        @NexusDevice.from_dictionary(
            {
                "nx_class": "NXdetector",
                "data": {
                    "nx_class": "NXobject",
                    "second_data_level_that_shouldnt_exist": {
                        "nx_class": "NXfield",
                        "data_key": "channel-1-mode",
                    },
                },
            }
        )
        class NxSimPointDetector(SimPointDetector):
            pass


def test_attempt_with_unknown_schema_from_client():
    with pytest.raises(
        TypeError,
        match=(
            "Requested `nx_class: NXbanana` but this isn't defined with pydantic "
            "schemas:"
        ),
    ):

        @NexusDevice.from_dictionary({"nx_class": "NXbanana", "length": "length"})
        class BananaMotor(SynAxis):
            pass


def test_schema_addition():
    nx_group = NxBase.from_dict(
        {
            "nx_class": "NXgroup",
            "@nx_group_constant_attribute": {"constant": "nx_group_constant"},
            "SUB_GROUP": {
                "nx_class": "NXgroup",
                "field1": {
                    "nx_class": "NXfield",
                    "data_key": "nx_group_data_key1",
                    "@attribute11": "nx_group_attribute11",
                },
            },
            "field2": {
                "nx_class": "NXfield",
                "data_key": "nx_group_data_key2",
                "@attribute21": "nx_group_attribute21",
                "@attribute22": "nx_group_attribute22",
            },
        }
    )
    nx_object = NxBase.from_dict(
        {
            "nx_class": "NXobject",
            "@nx_group_constant_attribute": {"hints_key": "nx_object_hints_key"},
            "@nx_object_constant_attribute": {"constant": "nx_object_constant"},
            "SUB_GROUP": {
                "nx_class": "NXobject",
                "field1": {
                    "nx_class": "NXfield",
                    "data_key": "nx_object_data_key1",
                    "@attribute11": "nx_object_attribute11",
                    "@attribute12": "nx_object_attribute12",
                },
                "field2": {
                    "nx_class": "NXfield",
                    "data_key": "nx_object_data_key3",
                    "@attribute31": "nx_object_attribute31",
                },
            },
            "field2": {
                "nx_class": "NXfield",
                "data_key": "nx_object_data_key2",
                "@attribute21": "nx_object_attribute21",
                "@attribute22": "nx_object_attribute22",
            },
        }
    )

    assert (nx_group + nx_object).model_dump() == {
        "@nx_group_constant_attribute": {
            "constant": "nx_group_constant",
            "data_key": None,
            "hints_key": None,
            "name": "@nx_group_constant_attribute",
        },
        "@nx_object_constant_attribute": {
            "constant": "nx_object_constant",
            "data_key": None,
            "hints_key": None,
            "name": "@nx_object_constant_attribute",
        },
        "SUB_GROUP": {
            "field1": {
                "@attribute11": {
                    "constant": "nx_group_attribute11",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute11",
                },
                "@attribute12": {
                    "constant": "nx_object_attribute12",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute12",
                },
                "data_key": "nx_group_data_key1",
                "nx_alias": "field1",
                "nx_class": "NXfield",
            },
            "field2": {
                "@attribute31": {
                    "constant": "nx_object_attribute31",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute31",
                },
                "data_key": "nx_object_data_key3",
                "nx_alias": "field2",
                "nx_class": "NXfield",
            },
            "nx_class": "NXgroup",
        },
        "field2": {
            "@attribute21": {
                "constant": "nx_group_attribute21",
                "data_key": None,
                "hints_key": None,
                "name": "@attribute21",
            },
            "@attribute22": {
                "constant": "nx_group_attribute22",
                "data_key": None,
                "hints_key": None,
                "name": "@attribute22",
            },
            "data_key": "nx_group_data_key2",
            "nx_alias": "field2",
            "nx_class": "NXfield",
        },
        "nx_class": "NXgroup",
    }

    assert (nx_object + nx_group).model_dump() == {
        "@nx_group_constant_attribute": {
            "constant": None,
            "data_key": None,
            "hints_key": "nx_object_hints_key",
            "name": "@nx_group_constant_attribute",
        },
        "@nx_object_constant_attribute": {
            "constant": "nx_object_constant",
            "data_key": None,
            "hints_key": None,
            "name": "@nx_object_constant_attribute",
        },
        "SUB_GROUP": {
            "field1": {
                "@attribute11": {
                    "constant": "nx_object_attribute11",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute11",
                },
                "@attribute12": {
                    "constant": "nx_object_attribute12",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute12",
                },
                "data_key": "nx_object_data_key1",
                "nx_alias": "field1",
                "nx_class": "NXfield",
            },
            "field2": {
                "@attribute31": {
                    "constant": "nx_object_attribute31",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attribute31",
                },
                "data_key": "nx_object_data_key3",
                "nx_alias": "field2",
                "nx_class": "NXfield",
            },
            "nx_class": "NXobject",
        },
        "field2": {
            "@attribute21": {
                "constant": "nx_object_attribute21",
                "data_key": None,
                "hints_key": None,
                "name": "@attribute21",
            },
            "@attribute22": {
                "constant": "nx_object_attribute22",
                "data_key": None,
                "hints_key": None,
                "name": "@attribute22",
            },
            "data_key": "nx_object_data_key2",
            "nx_alias": "field2",
            "nx_class": "NXfield",
        },
        "nx_class": "NXobject",
    }
