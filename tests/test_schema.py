import pytest
from ophyd.sim import SynAxis
from ophyd_async.sim import SimPointDetector
from pydantic import ValidationError

from bluesky_nexus import NexusDevice


def test_writer_behaviour_with_failing_schema():
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


def test_attempt_with_unknown_schema():
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
