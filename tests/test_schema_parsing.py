from pathlib import Path

import pytest
from bluesky import RunEngine
from bluesky import plan_stubs as bps
from bluesky import plans as bp
from ophyd_async.core import StandardReadable, StandardReadableFormat, soft_signal_rw
from ophyd_async.sim import SimMotor, SimPointDetector

from bluesky_nexus import NexusDevice

from . import load_only_generated_nexus_file


def test_example_schema_and_manual_schema_with_equivalence(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    """Checks that the autofilled schema is equivalent to what we're expecting."""

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>-channel-1-value": None,
            "<name>-channel-2-value": None,
        }
    )
    class SimPointDetectorWithSchema(SimPointDetector):
        pass

    RE_directly_subscribed(
        bp.count(
            [
                SimPointDetectorWithSchema(None, name="sim_point_detector_with_schema"),
                SimPointDetector(None, name="sim_point_detector_without_schema"),
            ],
            num=3,
        )
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    sim_point_detector_with_some_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]
    sim_point_detector_with_without_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]

    assert (
        list(sim_point_detector_with_some_schema)
        == list(sim_point_detector_with_without_schema)
        == [
            "channel-1-mode",
            "channel-1-value",
            "channel-2-mode",
            "channel-2-value",
            "channel-3-mode",
            "channel-3-value",
        ]
    )


def test_simple_nx_detector(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXdetector",
            "data": {"nx_class": "NXfield", "datakey": "<name>-channel-1-value"},
        }
    )
    class NxSimPointDetector(SimPointDetector):
        pass

    detector = NxSimPointDetector(None, name="detector")
    RE_directly_subscribed(
        bp.count(
            [detector],
            num=3,
        )
    )

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["detector"]

    assert list(loaded) == [
        "channel-1-mode",
        "channel-2-mode",
        "channel-2-value",
        "channel-3-mode",
        "channel-3-value",
        "data",
    ]
    assert list(loaded["data"]) == [290, 290, 290]


@pytest.mark.parametrize(
    ("passed_alias", "expected_alias"), [(None, "<name>"), ("some_alias", "some_alias")]
)
def test_device_with_only_one_field_schema(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
    passed_alias: str | None,
    expected_alias: str,
):
    """Demonstrates that the tree structure doesn't require a group."""

    @NexusDevice.from_dictionary(
        {"nx_class": "NXfield", "datakey": "<name>", "nx_alias": passed_alias}
    )
    class MyPositioner(StandardReadable):
        def __init__(self, name: str):
            with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
                self.signal = soft_signal_rw(int)
            with self.add_children_as_readables(StandardReadableFormat.CHILD):
                self.other_signal_which_wont_end_up_in_nexus = soft_signal_rw(int)
            super().__init__(name=name)
            self.signal.set_name(name)

    device = MyPositioner(name="my_positioner")
    assert device.hints == {
        "NX_class": "NXfield",
        "NX_schema": {
            "datakey": "<name>",
            "nx_alias": expected_alias,
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "fields": ["my_positioner"],
    }
    RE_directly_subscribed(bp.count([device], num=3))
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]
    assert list(loaded) == ["description", "my_positioner", "read_times"]
    assert list(loaded["my_positioner"]) == [0, 0, 0]


def test_nexus_writer_on_signals(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    some_signal = soft_signal_rw(int, name="some_signal")
    another_signal = soft_signal_rw(int, name="another_signal")
    motor = SimMotor(name="motor")

    RE_directly_subscribed(bp.count([some_signal, another_signal, motor], num=3))

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]
    assert list(loaded) == [
        "another_signal",
        "description",
        "motor",
        "read_times",
        "some_signal",
    ]
    assert list(loaded["another_signal"]) == [0, 0, 0]
    assert loaded["another_signal"].attrs == {}
    assert list(loaded["motor"]) == ["acceleration_time", "motor", "velocity"]
    assert loaded["motor"].attrs == {"nxclass": "NXobject"}
