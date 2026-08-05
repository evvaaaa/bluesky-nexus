"""Tests schema validation on the device layer, without a writer."""

import pytest
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd.sim import SynAxis
from ophyd_async.sim import SimPointDetector
from pydantic import ValidationError

from bluesky_nexus import NexusDevice


@pytest.mark.parametrize(
    ("datakey_subset", "expected_alias"),
    (
        # Full schema definition.
        (
            {"some_alias": {"nx_class": "NXfield", "datakey": "<name>-signal"}},
            "some_alias",
        ),
        # Just the datakey.
        ({"<name>-signal": None}, "signal"),
        # Just the alias.
        ({"some_alias": "<name>-signal"}, "some_alias"),
    ),
)
def test_methods_of_declaring_datakeys(datakey_subset: dict, expected_alias: str):
    dictionary_schema = {"nx_class": "NXobject"}
    dictionary_schema.update(datakey_subset)

    @NexusDevice.from_dictionary(dictionary_schema)
    class SomeDevice(Device):
        signal = Cpt(EpicsSignal, "SIGNAL")

    assert SomeDevice(name="foo").hints == {
        "NX_class": "NXobject",
        "NX_schema": {
            expected_alias: {
                "datakey": "<name>-signal",
                "nx_alias": expected_alias,
                "nx_units": None,
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
                        "datakey": "<name>-channel-1-mode",
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

        @NexusDevice.from_dictionary(
            {"nx_class": "NXbanana", "length": "<name>-length"}
        )
        class BananaMotor(SynAxis):
            pass
