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


def test_structure(RE_directly_subscribed: RunEngine, tmpdir: Path) -> None:
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
        assert list(devices) == [f"some_{stream_name}_pv_positioner"]
        assert devices[f"some_{stream_name}_pv_positioner"].nxclass == "NXgroup"

        stream_info = stream["stream_info"]
        assert stream_info.nxclass == "NXcollection"
        assert list(stream_info) == ["descriptor", "time"]
        assert stream_info["descriptor"].nxclass == "NXcollection"


def test_example_schema_and_manual_schema_with_equivalence(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
) -> None:
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
) -> None:
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXdetector",
            "data": {"data_key": "channel-1-value"},
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

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]["detector"]

    assert list(loaded) == [
        "channel-1-mode",
        "channel-2-mode",
        "channel-2-value",
        "channel-3-mode",
        "channel-3-value",
        "data",
    ]
    assert list(loaded["data"]) == ["time", "value"]
    assert list(loaded["data"]["value"]) == [290, 290, 290]


def test_nexus_writer_on_signals(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
) -> None:
    some_signal = soft_signal_rw(int, name="some_signal")
    another_signal = soft_signal_rw(int, name="another_signal")
    motor = SimMotor(name="motor")

    RE_directly_subscribed(bp.count([some_signal, another_signal, motor], num=3))

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == [
        "another_signal",
        "motor",
        "some_signal",
    ]
    assert list(loaded["another_signal"]["value"]) == [0, 0, 0]
    assert loaded["another_signal"].attrs == {}
    assert list(loaded["motor"]) == ["acceleration_time", "motor", "velocity"]
    assert loaded["motor"].attrs == {"nxclass": "NXobject"}


def test_schema_client_server_differing_schema(
    RE_subscribed_over_zmq: RunEngine, tmpdir: Path
) -> None:
    new_motor_schema = {"@nxclass": "NXnew", "some_data": "foo"}

    with pytest.raises(
        TypeError,
        match=("Requested `@nxclass: NXnew` but this isn't defined with pydantic schemas:"),
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
    assert list(loaded["motor"]["motor"]["value"]) == [0, 0, 0]


def test_constant_attributes(RE_directly_subscribed: RunEngine, tmpdir) -> None:
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "@description": "Some constant description",
            "sim_motor_with_description": {
                "data_key": "",
                "@units": "overriden",
                "@long_name": "Long motor name",
                "@non_standard_attr": 7,
            },
        }
    )
    class SimMotorWithDescription(SynAxis): ...

    sim_motor_with_description = SimMotorWithDescription(name="sim_motor_with_description")
    sim_motor = SimMotor(name="sim_motor")
    RE_directly_subscribed(bp.count([sim_motor, sim_motor_with_description], num=3))  # type: ignore

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == [
        "sim_motor",
        "sim_motor_with_description",
    ]
    assert list(loaded["sim_motor"].attrs) == ["nxclass"]
    assert list(loaded["sim_motor_with_description"].attrs) == [
        "description",
        "nxclass",
    ]
    assert loaded["sim_motor_with_description"].attrs["description"] == "Some constant description"
    assert list(loaded["sim_motor"]["sim_motor"]["value"].attrs) == ["units"]
    assert loaded["sim_motor"]["sim_motor"]["value"].attrs["units"] == "mm"

    assert list(
        loaded["sim_motor_with_description"]["sim_motor_with_description"]["value"].attrs
    ) == [
        "long_name",
        "non_standard_attr",
        "units",
    ]

    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"]["value"].attrs[
            "non_standard_attr"
        ]
        == 7
    )
    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"]["value"].attrs["units"]
        == "overriden"
    )
    assert (
        loaded["sim_motor_with_description"]["sim_motor_with_description"]["value"].attrs[
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
    ]
    assert list(loaded["syn_axis_missing_metadata"].attrs) == ["nxclass"]
    assert list(loaded["syn_axis_with_description"].attrs) == ["description", "nxclass"]
    assert loaded["syn_axis_with_description"].attrs["description"] == "Some description..."


def test_attributes_from_data_keys(RE_directly_subscribed: RunEngine, tmpdir):
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "readback": {
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
            [ADeviceForAnUnfortunatelyDesignedIOCWhereUnitsArentInDotEgu(name="device")],
            num=3,
        )
    )
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    # Egu is still included as a field even if it's been added as
    # an attribute to another field.
    assert list(loaded["device"]) == ["egu", "readback"]
    assert list(loaded["device"]["readback"]["value"].attrs) == ["units"]
    assert loaded["device"]["readback"]["value"].attrs["units"] == "Oz"


# TODO: Currently the nexusformat validator doesn't seem capable of this.
# def test_passing_bluesky_nexus_nx_schema_but_incorrect_nexusformat_definitions(
#     RE_directly_subscribed: RunEngine, tmpdir, caplog: pytest.LogCaptureFixture
# ):
#     @add_nx_class_basemodel
#     class NxData(NxGroup):
#         data: NxObject  # A NXdata should contain a single field for `data:`
#
#     @NexusDevice.from_pydantic_schema(
#         NxData(data=NxObject(some_data_key=NxField(data_key="user_readback")))
#     )
#     class SomeSimMotor(SimMotor): ...
#
#     RE_directly_subscribed(bp.count([SomeSimMotor(name="sim_motor")]))
#     assert (
#         "Created a nexus structure for sim_motor but it cannot be validated against the "
#         "nexusformat definitions. A default NXObject will be used..."
#     ) in caplog.text
#     loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]["sim_motor"]
#     assert loaded.attrs == {"nxclass": "NXobject"}
#     assert list(loaded) == ["acceleration_time", "sim_motor", "velocity"]
