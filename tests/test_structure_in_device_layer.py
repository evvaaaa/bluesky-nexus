"""Tests schema validation on the device layer, without a writer."""

from __future__ import annotations

from pathlib import Path

import pytest
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd.sim import SynAxis
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from ophyd_async.sim import SimPointDetector
from pydantic import ValidationError

from bluesky_nexus import NexusDevices
from bluesky_nexus.nx_schema import (
    NxAttribute,
    NxBase,
    NxField,
    NxGroup,
    NxSubEntry,
    add_nx_class_basemodel,
)


@pytest.mark.parametrize(
    ("argument"),
    (
        "some_schema.yaml",
        Path("some_schema.yaml"),
        (Path(__file__).parent.absolute() / "some_schema.yaml"),
        {
            "$nxclass": "NXgroup",
            "SOME_SUBGROUP": {"$nxclass": "NXsubentry", "some_data_key": "some_data_key_value"},
            "$some_attribute": "some_attribute_value",
            "another_data_key": "another_data_key_value",
        },
        NxGroup(
            SOME_SUBGROUP=NxSubEntry(some_data_key=NxField(data_key="some_data_key_value")),
            some_attribute=NxAttribute(constant="some_attribute_value"),
            another_data_key=NxField(data_key="another_data_key_value"),
        ),
    ),
)
def test_methods_of_loading_schema(argument) -> None:
    @NexusDevices.add_device_from_schema(argument)
    class SomeDevice(Device): ...

    assert SomeDevice("X", name="device").hints == {
        "NX_class": "NXgroup",
        "NX_schema": {
            "$nxclass": "NXgroup",
            "$some_attribute": "some_attribute_value",
            "SOME_SUBGROUP": {"$nxclass": "NXsubentry", "some_data_key": "some_data_key_value"},
            "another_data_key": "another_data_key_value",
        },
        "fields": [],
    }


def test_loading_schema_from_a_non_existent_path() -> None:
    with pytest.raises(
        ValueError, match=r"Path `/.*/tests/some_sub_package/my_schema.yaml` does not exist\."
    ):  # Becomes absolute, includin root.

        @NexusDevices.add_device_from_path("some_sub_package/my_schema.yaml")
        class SomeDevice(Device): ...


@pytest.mark.parametrize(
    ("data_key_subset"),
    (
        # Full schema definition.
        {"some_alias": {"data_key": "signal"}},
        {"some_alias": "signal"},  # Just the alias.
    ),
)
def test_methods_of_declaring_data_keys(data_key_subset: dict) -> None:
    dictionary_schema = {"$nxclass": "NXsubentry"}
    dictionary_schema.update(data_key_subset)

    @NexusDevices.add_device_from_dictionary(dictionary_schema)
    class SomeDevice(Device):
        signal = Cpt(EpicsSignal, "SIGNAL")

    assert SomeDevice(name="foo").hints == {
        "NX_class": "NXsubentry",
        "NX_schema": {
            "some_alias": "signal",
            "$nxclass": "NXsubentry",
        },
        "fields": [],
    }


def test_writer_behaviour_with_failing_schema_specified_in_yaml() -> None:
    with pytest.raises(
        ValidationError,
        match=("Input should be a valid dictionary or instance of NxField"),
    ):

        @NexusDevices.add_device_from_dictionary(
            {
                "$nxclass": "NXdetector",
                "data": {
                    "$nxclass": "NXsubentry",
                    "second_data_level_that_shouldnt_exist": {
                        "data_key": "channel-1-mode",
                    },
                },
            }
        )
        class NxSimPointDetector(SimPointDetector):
            pass


def test_attempt_with_unknown_schema_from_client() -> None:
    with pytest.raises(
        TypeError,
    ) as excinfo:

        @NexusDevices.add_device_from_dictionary({"$nxclass": "NXbanana", "length": "length"})
        class BananaMotor(SynAxis):
            pass

    assert "Requested `$nxclass: NXbanana` but this isn't defined with pydantic schemas:" in str(
        excinfo
    )


def test_schema_addition() -> None:
    nx_group = NxBase.from_dictionary(
        {
            "$nxclass": "NXgroup",
            "$nx_group_constant_attribute": {"constant": "nx_group_constant"},
            "SUB_GROUP": {
                "$nxclass": "NXgroup",
                "field1": {
                    "data_key": "nx_group_data_key1",
                    "$attribute11": "nx_group_attribute11",
                },
            },
            "field2": {
                "data_key": "nx_group_data_key2",
                "$attribute21": "nx_group_attribute21",
                "$attribute22": "nx_group_attribute22",
            },
        }
    )
    nx_object = NxBase.from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "$nx_group_constant_attribute": {"hints_key": "nx_object_hints_key"},
            "$nx_object_constant_attribute": {"constant": "nx_object_constant"},
            "SUB_GROUP": {
                "$nxclass": "NXsubentry",
                "field1": {
                    "data_key": "nx_object_data_key1",
                    "$attribute11": "nx_object_attribute11",
                    "$attribute12": "nx_object_attribute12",
                },
                "field2": {
                    "data_key": "nx_object_data_key3",
                    "$attribute31": "nx_object_attribute31",
                },
            },
            "field2": {
                "data_key": "nx_object_data_key2",
                "$attribute21": "nx_object_attribute21",
                "$attribute22": "nx_object_attribute22",
            },
        }
    )

    assert (nx_group + nx_object).model_dump() == {
        "$nx_group_constant_attribute": "nx_group_constant",
        "$nx_object_constant_attribute": "nx_object_constant",
        "$nxclass": "NXgroup",
        "SUB_GROUP": {
            "$nxclass": "NXgroup",
            "field1": {
                "$attribute11": "nx_group_attribute11",
                "$attribute12": "nx_object_attribute12",
                "data_key": "nx_group_data_key1",
            },
            "field2": {
                "$attribute31": "nx_object_attribute31",
                "data_key": "nx_object_data_key3",
            },
        },
        "field2": {
            "$attribute21": "nx_group_attribute21",
            "$attribute22": "nx_group_attribute22",
            "data_key": "nx_group_data_key2",
        },
    }

    assert (nx_object + nx_group).model_dump() == {
        "$nx_group_constant_attribute": {
            "constant": None,
            "data_key": None,
            "hints_key": "nx_object_hints_key",
        },
        "$nx_object_constant_attribute": "nx_object_constant",
        "$nxclass": "NXsubentry",
        "SUB_GROUP": {
            "$nxclass": "NXsubentry",
            "field1": {
                "$attribute11": "nx_object_attribute11",
                "$attribute12": "nx_object_attribute12",
                "data_key": "nx_object_data_key1",
            },
            "field2": {
                "$attribute31": "nx_object_attribute31",
                "data_key": "nx_object_data_key3",
            },
        },
        "field2": {
            "$attribute21": "nx_object_attribute21",
            "$attribute22": "nx_object_attribute22",
            "data_key": "nx_object_data_key2",
        },
    }

    assert (nx_object + nx_object) == nx_object


def test_serialization_deserialization() -> None:
    @add_nx_class_basemodel
    class NxTestGroup(NxGroup):
        constant_attribute_shorthand: NxAttribute
        constant_attribute: NxAttribute
        datakey_attribute: NxAttribute
        hints_attribute: NxAttribute
        field_shorthand: NxField
        field: NxField
        SUB_GROUP_NOT_REQUIRED: NxTestGroup | None = None

    test_nx_group_fields = {
        "$nxclass": "NXtestgroup",
        "$constant_attribute_shorthand": "some_constant_shorthand",
        "$constant_attribute": {"constant": "some_constant"},
        "$datakey_attribute": {"data_key": "some_attribute_datakey"},
        "$hints_attribute": {"hints_key": ["some", "hints", "key"]},
        "field_shorthand": "some_field_datakey_shorthand",
        "field": {
            "data_key": "some_field_datakey",
            "$some_field_attribute": "some_field_attribute",
        },
    }
    test_nx_group_fields.update({"SUB_GROUP_NOT_REQUIRED": test_nx_group_fields.copy()})

    nx_group_from_base = NxBase.from_dictionary(test_nx_group_fields)
    nx_group_refined = NxTestGroup.from_dictionary(test_nx_group_fields)
    assert (
        isinstance(nx_group_from_base, NxTestGroup)
        and isinstance(nx_group_refined, NxTestGroup)
        and isinstance(nx_group_refined.SUB_GROUP_NOT_REQUIRED, NxTestGroup)
    )

    for group in (
        nx_group_from_base,
        nx_group_refined,
        nx_group_refined.SUB_GROUP_NOT_REQUIRED,
    ):
        assert group.nxclass == NxAttribute(constant="NXtestgroup")
        assert group.constant_attribute_shorthand == NxAttribute(
            constant="some_constant_shorthand"
        )
        assert group.constant_attribute == NxAttribute(constant="some_constant")
        assert group.datakey_attribute == NxAttribute(data_key="some_attribute_datakey")
        assert group.hints_attribute == NxAttribute(hints_key=["some", "hints", "key"])
        assert group.field_shorthand == NxField(data_key="some_field_datakey_shorthand")
        assert group.field == NxField(
            data_key="some_field_datakey",
            some_field_attribute=NxAttribute(constant="some_field_attribute"),  # type: ignore
        )

    assert nx_group_from_base.model_dump() == {
        "$constant_attribute": "some_constant",
        "$constant_attribute_shorthand": "some_constant_shorthand",
        "$datakey_attribute": {
            "constant": None,
            "data_key": "some_attribute_datakey",
            "hints_key": None,
        },
        "$hints_attribute": {
            "constant": None,
            "data_key": None,
            "hints_key": ["some", "hints", "key"],
        },
        "$nxclass": "NXtestgroup",
        "SUB_GROUP_NOT_REQUIRED": {
            "$constant_attribute": "some_constant",
            "$constant_attribute_shorthand": "some_constant_shorthand",
            "$datakey_attribute": {
                "constant": None,
                "data_key": "some_attribute_datakey",
                "hints_key": None,
            },
            "$hints_attribute": {
                "constant": None,
                "data_key": None,
                "hints_key": ["some", "hints", "key"],
            },
            "$nxclass": "NXtestgroup",
            "SUB_GROUP_NOT_REQUIRED": None,
            "field": {
                "$some_field_attribute": "some_field_attribute",
                "data_key": "some_field_datakey",
            },
            "field_shorthand": "some_field_datakey_shorthand",
        },
        "field": {
            "$some_field_attribute": "some_field_attribute",
            "data_key": "some_field_datakey",
        },
        "field_shorthand": "some_field_datakey_shorthand",
    }
    assert NxGroup.from_dictionary(nx_group_from_base.model_dump()) == nx_group_from_base


def test_acceptable_nx_data_specification():
    @NexusDevices.add_device_from_schema(
        {
            "$nxclass": "NXdata",
            "$signal": "some_signal_name",
            "$axes": ["some_axis_name_1", "some_axis_name_2"],
            "some_signal_name": "signal",
            "some_axis_name_1": "axis_signal_1",
            "some_axis_name_2": "axis_signal_2",
        }
    )
    class SomeDetector(StandardReadable):
        def __init__(self, name: str = "") -> None:
            super().__init__(name)
            with self.add_children_as_readables():
                self.axis_signal_1, _ = soft_signal_r_and_setter(int)
                self.axis_signal_2, _ = soft_signal_r_and_setter(int)
                self.signal, _ = soft_signal_r_and_setter(int)


@pytest.mark.parametrize(
    ("specification", "exception_cls", "exception_text"),
    [
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
            },
            ValidationError,
            "axes\n  Field required",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$axes": ["axis_signal_1"],
            },
            ValidationError,
            "signal\n  Field required",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", 2],
            },
            ValidationError,
            "Input should be a valid string [type=string_type, input_value=2, input_type=int]",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", "axis_signal_2"],
            },
            ValidationError,
            "Specified a signal some_signal_name as the NxData signal attribute but no",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", "axis_signal_2"],
                "some_signal_name": "some_data_key",
            },
            ValidationError,
            "Specified an axis axis_signal_1 in the NxData axes attribute but no axis",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": {"data_key": "some_data_key"},
                "$axes": ["axis_signal_1", "axis_signal_2"],
                "some_signal_name": "signal",
                "some_axis_name_1": "axis_signal_1",
                "some_axis_name_2": "axis_signal_2",
            },
            ValidationError,
            "signal.data_key\n  Input should be None",
        ),
    ],
)
def test_nx_data_incorrect_specification(
    specification: dict, exception_cls: type[Exception], exception_text: str
):
    with pytest.raises(exception_cls) as excinfo:

        @NexusDevices.add_device_from_schema(specification)
        class SomeDetector(StandardReadable):
            def __init__(self, name: str = "") -> None:
                super().__init__(name)
                with self.add_children_as_readables():
                    self.axis_signal_1, _ = soft_signal_r_and_setter(int)
                    self.axis_signal_2, _ = soft_signal_r_and_setter(int)
                    self.signal, _ = soft_signal_r_and_setter(int)

    assert exception_text in str(excinfo)
