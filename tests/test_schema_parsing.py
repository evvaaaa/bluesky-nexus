"""These tests are for how the schema is parsed/created in the writer."""

import re
from pathlib import Path

import pytest
from bluesky import RunEngine
from bluesky import plans as bp
from bluesky.preprocessors import baseline_wrapper
from nexusformat import nexus
from ophyd.sim import SynAxis
from ophyd_async.core import StandardReadable, StandardReadableFormat, soft_signal_rw
from ophyd_async.sim import SimMotor, SimPointDetector

from bluesky_nexus import NexusDevice, __version__
from bluesky_nexus.nx_schema import (
    NxField,
    NxGroup,
    add_nx_class_basemodel,
    NX_CLASS_TO_BASEMODEL,
)

from . import get_logs, load_only_generated_nexus_file, wait_for_nexus_file


def test_structure(RE_directly_subscribed: RunEngine, tmpdir: Path):
    some_primary_pv_positioner = SynAxis(name="some_primary_pv_positioner")
    some_baseline_pv_positioner = SynAxis(name="some_baseline_pv_positioner")

    RE_directly_subscribed(
        baseline_wrapper(
            bp.count([some_primary_pv_positioner], num=2),  # type: ignore
            [some_baseline_pv_positioner],
        )
    )

    loaded = wait_for_nexus_file(tmpdir)
    assert list(loaded) == ["entry"]
    entry = loaded["entry"]
    assert entry.nxclass == "NXentry"
    assert list(entry) == [
        "Application name",
        "Application version",
        "Content",
        "baseline",
        "primary",
        "run_info",
    ]
    assert entry["Application name"] == "bluesky_nexus"
    assert entry["Application version"] == __version__
    assert entry["Content"] == "A bluesky run's documents parsed to nexus."

    run_info = entry["run_info"]
    assert run_info.nxclass == "NXcollection"
    assert list(run_info) == ["run_start", "run_stop"]

    for stream_name in ("primary", "baseline"):
        stream = entry[stream_name]
        assert stream.nxclass == "NXsubentry"
        assert list(stream) == ["devices", "stream_info"]

        devices = stream["devices"]
        assert devices.nxclass == "NXinstrument"
        assert list(devices) == [f"some_{stream_name}_pv_positioner", "time"]
        assert devices[f"some_{stream_name}_pv_positioner"].nxclass == "NXgroup"
        assert devices["time"].nxclass == "NXdata"

        stream_info = stream["stream_info"]
        assert stream_info.nxclass == "NXcollection"
        assert list(stream_info) == ["descriptor", "timestamps"]
        assert stream_info["descriptor"].nxclass == "NXcollection"
        assert stream_info["timestamps"].nxclass == "NXsubentry"
        assert list(stream_info["timestamps"]) == [
            f"some_{stream_name}_pv_positioner",
            f"some_{stream_name}_pv_positioner_acceleration",
            f"some_{stream_name}_pv_positioner_setpoint",
            f"some_{stream_name}_pv_positioner_velocity",
        ]


def test_example_schema_and_manual_schema_with_equivalence(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    """Checks that the autofilled schema is equivalent to what we're expecting."""

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "channel-1-value": None,
            "channel-2-value": None,
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

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    sim_point_detector_with_some_schema = loaded["sim_point_detector_with_schema"]
    sim_point_detector_with_without_schema = loaded["sim_point_detector_with_schema"]

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
            "data": {"nx_class": "NXfield", "datakey": "channel-1-value"},
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

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"][
        "detector"
    ]

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
    ("passed_alias", "expected_alias"), [(None, ""), ("some_alias", "some_alias")]
)
def test_device_with_only_one_field_schema(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
    passed_alias: str | None,
    expected_alias: str,
):
    """Demonstrates that the tree structure doesn't require a group."""

    @NexusDevice.from_dictionary(
        {"nx_class": "NXfield", "datakey": "", "nx_alias": passed_alias}
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
            "datakey": "",
            "nx_alias": expected_alias,
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "fields": ["my_positioner"],
    }
    RE_directly_subscribed(bp.count([device], num=3))
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == ["my_positioner", "time"]
    assert list(loaded["my_positioner"]) == [0, 0, 0]


def test_nexus_writer_on_signals(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    some_signal = soft_signal_rw(int, name="some_signal")
    another_signal = soft_signal_rw(int, name="another_signal")
    motor = SimMotor(name="motor")

    RE_directly_subscribed(bp.count([some_signal, another_signal, motor], num=3))

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == [
        "another_signal",
        "motor",
        "some_signal",
        "time",
    ]
    assert list(loaded["another_signal"]) == [0, 0, 0]
    assert loaded["another_signal"].attrs == {}
    assert list(loaded["motor"]) == ["acceleration_time", "motor", "velocity"]
    assert loaded["motor"].attrs == {"nxclass": "NXobject"}


def test_schema_client_server_differing_schema(
    RE_subscribed_over_zmq: RunEngine, tmpdir: Path, monkeypatch
):
    new_motor_schema = {"nx_class": "NXnew", "some_data": "foo"}

    with pytest.raises(
        TypeError,
        match=(
            "Requested `nx_class: NXnew` but this isn't defined with pydantic schemas:"
        ),
    ):

        @NexusDevice.from_dictionary(new_motor_schema)
        class NewMotorWhichWillFail(SimMotor): ...

    monkeypatch.setattr(
        "bluesky_nexus.nx_schema.nx_base.NX_CLASS_TO_BASEMODEL",
        NX_CLASS_TO_BASEMODEL.copy(),
    )

    @add_nx_class_basemodel
    class NxNew(NxGroup):
        some_data: NxField

    # Passes because the nexus group was added in this process.
    @NexusDevice.from_dictionary(new_motor_schema)
    class NewMotor(SimMotor): ...

    motor = NewMotor(name="motor")
    RE_subscribed_over_zmq(bp.count([motor], num=3))
    loaded = wait_for_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    logs = get_logs(tmpdir).read_text()
    pattern = re.compile(
        (
            r".*?Received a malformed schema in motor\. The error was:\n\s+Requested "
            r"`nx_class: NXnew` but this isn't defined with pydantic schemas: "
            r"\{[^}]*\}\nA default schema will be used instead\."
        ),
        re.DOTALL,
    )

    # The subprocess didn't have the schema we made in this process, so it wrote a new
    # NXobject for the device after raising the error.
    assert pattern.search(logs)
    assert str(loaded["motor"].attrs["nxclass"]) == nexus.NXattr("NXobject")
    assert list(loaded["motor"]) == [
        "acceleration_time",
        "motor",
        "velocity",
    ]
    assert list(loaded["motor"]["motor"]) == [0, 0, 0]
