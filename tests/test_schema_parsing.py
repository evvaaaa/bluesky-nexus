"""These tests are for how the schema is parsed/created in the writer."""

import re
from pathlib import Path

import pytest
from bluesky import RunEngine
from bluesky import plans as bp
from bluesky.preprocessors import baseline_wrapper
from nexusformat import nexus
from ophyd.sim import SynAxis
from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.core import (
    StandardReadableFormat as Fmt,
)
from ophyd_async.sim import SimMotor, SimPointDetector

from bluesky_nexus import NexusDevice, __version__
from bluesky_nexus.nx_schema import (
    NxField,
    NxGroup,
    add_nx_class_basemodel,
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
            "@nxclass": "NXobject",
            "channel-1-value": "channel-1-value",
            "channel-2-value": "channel-2-value",
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
            "@nxclass": "NXdetector",
            "data": {"@nxclass": "NXfield", "data_key": "channel-1-value"},
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
        {"@nxclass": "NXfield", "data_key": "", "nx_alias": passed_alias}
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
            "data_key": "",
            "nx_alias": expected_alias,
            "@nxclass": "NXfield",
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
    RE_subscribed_over_zmq: RunEngine, tmpdir: Path
):
    new_motor_schema = {"@nxclass": "NXnew", "some_data": "foo"}

    with pytest.raises(
        TypeError,
        match=(
            "Requested `@nxclass: NXnew` but this isn't defined with pydantic schemas:"
        ),
    ):

        @NexusDevice.from_dictionary(new_motor_schema)
        class NewMotorWhichWillFail(SimMotor): ...

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
            r"`@nxclass: NXnew` but this isn't defined with pydantic schemas: "
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


def test_constant_attributes(RE_directly_subscribed: RunEngine, tmpdir):
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "@description": "Some constant description",
            "sim_motor_with_description": {
                "@nxclass": "NXfield",
                "data_key": "",
                "@units": "overriden",
                "@long_name": "Long motor name",
                "@non_standard_attr": 7,
            },
        }
    )
    class SimMotorWithDescription(SynAxis): ...

    sim_motor_with_description = SimMotorWithDescription(
        name="sim_motor_with_description"
    )
    sim_motor = SimMotor(name="sim_motor")
    RE_directly_subscribed(bp.count([sim_motor, sim_motor_with_description], num=3))  # type: ignore

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == [
        "sim_motor",
        "sim_motor_with_description",
        "time",
    ]
    assert list(loaded["sim_motor"].attrs) == ["nxclass"]
    assert list(loaded["sim_motor_with_description"].attrs) == [
        "description",
        "nxclass",
    ]
    assert (
        loaded["sim_motor_with_description"].attrs["description"]
        == "Some constant description"
    )
    assert list(loaded["sim_motor"]["sim_motor"].attrs) == ["units"]
    assert loaded["sim_motor"]["sim_motor"].attrs["units"] == "mm"

    assert list(
        loaded["sim_motor_with_description"]["sim_motor_with_description"].attrs
    ) == [
        "long_name",
        "non_standard_attr",
        "units",
    ]

    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"].attrs[
            "non_standard_attr"
        ]
        == 7
    )
    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"].attrs[
            "units"
        ]
        == "overriden"
    )
    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"].attrs[
            "long_name"
        ]
        == "Long motor name"
    )


def test_attributes_from_hints(RE_directly_subscribed: RunEngine, tmpdir):
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "@description": {"hints_key": ["md", "description"]},
        }
    )
    class SynAxisWithDescription(SynAxis): ...

    syn_axis_with_description = SynAxisWithDescription(name="syn_axis_with_description")
    syn_axis_with_description.md = {"description": "Some description..."}
    syn_axis_missing_metadata = SynAxisWithDescription(name="syn_axis_missing_metadata")
    RE_directly_subscribed(
        bp.count([syn_axis_with_description, syn_axis_missing_metadata], num=3)  # type: ignore
    )
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == [
        "syn_axis_missing_metadata",
        "syn_axis_with_description",
        "time",
    ]
    assert list(loaded["syn_axis_missing_metadata"].attrs) == ["nxclass"]
    assert list(loaded["syn_axis_with_description"].attrs) == ["description", "nxclass"]
    assert (
        loaded["syn_axis_with_description"].attrs["description"]
        == "Some description..."
    )


def test_attributes_from_data_keys(RE_directly_subscribed: RunEngine, tmpdir):
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "readback": {
                "@nxclass": "NXfield",
                "data_key": "readback",
                "@units": {"data_key": "egu"},
            },
        }
    )
    class ADeviceForAnUnfortunatelyDesignedIOCWhereUnitsArentInDotEgu(StandardReadable):
        def __init__(self, name: str = "") -> None:
            super().__init__(name)
            with self.add_children_as_readables(format=Fmt.CONFIG_SIGNAL):
                self.egu, _ = soft_signal_r_and_setter(str, initial_value="Oz")
            with self.add_children_as_readables(format=Fmt.CHILD):
                self.readback, _ = soft_signal_r_and_setter(float)

    RE_directly_subscribed(
        bp.count(
            [
                ADeviceForAnUnfortunatelyDesignedIOCWhereUnitsArentInDotEgu(
                    name="device"
                )
            ],
            num=3,
        )
    )
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    # Egu is still included as a field even if it's been added as
    # an attribute to another field.
    assert list(loaded["device"]) == ["egu", "readback"]
    assert list(loaded["device"]["readback"].attrs) == ["units"]
    assert loaded["device"]["readback"].attrs["units"] == "Oz"
