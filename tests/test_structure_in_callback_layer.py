"""These tests are for how the schema is parsed/created in the writer."""

import re
from pathlib import Path
from time import time

import numpy as np
import pytest
from bluesky import RunEngine
from bluesky import plans as bp
from bluesky.preprocessors import baseline_wrapper
from cycler import cycler
from nexusformat import nexus
from numpy import sin
from ophyd.sim import SynAxis
from ophyd_async.core import (
    StandardReadable,
    callback_on_mock_put,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.core import StandardReadableFormat as Fmt
from ophyd_async.plan_stubs import ensure_connected
from ophyd_async.sim import SimMotor, SimPointDetector

from bluesky_nexus import NexusDevices, __version__
from bluesky_nexus.base_schema import (
    NxField,
    NxGroup,
    add_nx_class_basemodel,
)

from . import (
    add_device_metadata_to_hints_wrapper,
    get_logs,
    load_only_generated_nexus_file,
    wait_for_nexus_file,
)


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
        assert stream.nxclass == "NXcollection"
        assert list(stream) == ["devices", "stream_info"]

        devices = stream["devices"]
        assert devices.nxclass == "NXinstrument"
        assert list(devices) == [f"some_{stream_name}_pv_positioner"]
        assert devices[f"some_{stream_name}_pv_positioner"].nxclass == "NXsubentry"

        stream_info = stream["stream_info"]
        assert stream_info.nxclass == "NXcollection"
        assert list(stream_info) == ["descriptor", "time"]
        assert stream_info["descriptor"].nxclass == "NXcollection"


def test_example_schema_and_manual_schema_with_equivalence(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
) -> None:
    """Checks that the autofilled schema is equivalent to what we're expecting."""

    @NexusDevices.add_device_from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "channel_1_value": "channel-1-value",
            "channel_2_value": "channel-2-value",
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
            "channel_1_mode",
            "channel_1_value",
            "channel_2_mode",
            "channel_2_value",
            "channel_3_mode",
            "channel_3_value",
        ]
    )


def test_simple_nx_detector(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
) -> None:
    @NexusDevices.add_device_from_dictionary(
        {
            "$nxclass": "NXdetector",
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
        "channel_1_mode",
        "channel_2_mode",
        "channel_2_value",
        "channel_3_mode",
        "channel_3_value",
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
    assert {k: str(v) for k, v in loaded["another_signal"].attrs.items()} == {
        "axes": "timestamps",
        "signal": "value",
    }
    assert list(loaded["motor"]) == ["acceleration_time", "motor", "velocity"]
    assert {k: str(v) for k, v in loaded["motor"].attrs.items()} == {"nxclass": "NXsubentry"}


def test_schema_client_server_differing_schema(
    RE_subscribed_over_zmq: RunEngine, tmpdir: Path
) -> None:
    new_motor_schema = {"$nxclass": "NXnew", "some_data": "foo"}

    with pytest.raises(TypeError) as excinfo:

        @NexusDevices.add_device_from_dictionary(new_motor_schema)
        class NewMotorWhichWillFail(SimMotor): ...

    # Can't use match with literal "\$" for whatever reason...
    assert "Requested `$nxclass: NXnew` but this isn't defined with pydantic schemas: " in str(
        excinfo
    )

    @add_nx_class_basemodel
    class NxNew(NxGroup):
        some_data: NxField

    # Passes because the nexus group was added in this process.
    @NexusDevices.add_device_from_dictionary(new_motor_schema)
    class NewMotor(SimMotor): ...

    motor = NewMotor(name="motor")
    RE_subscribed_over_zmq(bp.count([motor], num=3))
    loaded = wait_for_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    logs = get_logs(tmpdir).read_text()
    pattern = re.compile(
        (
            r".*?Received a malformed schema in motor\. The error was:\n\s+Requested "
            r"`\$nxclass: NXnew` but this isn't defined with pydantic schemas: "
            r"\{[^}]*\}\nA default schema will be used instead\."
        ),
        re.DOTALL,
    )

    # The subprocess didn't have the schema we made in this process, so it wrote a new
    # NXsubentry for the device after raising the error.
    assert pattern.search(logs)
    assert str(loaded["motor"].attrs["nxclass"]) == nexus.NXattr("NXsubentry")
    assert list(loaded["motor"]) == [
        "acceleration_time",
        "motor",
        "velocity",
    ]
    assert list(loaded["motor"]["motor"]["value"]) == [0, 0, 0]


def test_constant_attributes(RE_directly_subscribed: RunEngine, tmpdir) -> None:
    @NexusDevices.add_device_from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "$description": "Some constant description",
            "sim_motor_with_description": {
                "data_key": "",
                "$units": "overriden",
                "$long_name": "Long motor name",
                "$non_standard_attr": 7,
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
    @add_device_metadata_to_hints_wrapper
    @NexusDevices.add_device_from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "description": {"hints_key": ["metadata", "description"]},
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
    assert set(loaded["syn_axis_missing_metadata"]) == {
        "acceleration",
        "setpoint",
        "syn_axis_missing_metadata",
        "velocity",
    }
    assert list(loaded["syn_axis_with_description"]) == [
        "acceleration",
        "description",
        "setpoint",
        "syn_axis_with_description",
        "velocity",
    ]
    assert loaded["syn_axis_with_description"]["description"] == "Some description..."


def test_attributes_from_data_keys(RE_directly_subscribed: RunEngine, tmpdir):
    @NexusDevices.add_device_from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "readback": {
                "data_key": "readback",
                "$units": {"data_key": "egu"},
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


# TODO: Commented out for now, see TODO in nx_structure._nexus_structure.add_stream_data_to_group
# def test_passing_bluesky_nexus_nx_schema_but_incorrect_nexusformat_definitions(
#     RE_directly_subscribed: RunEngine, tmpdir, caplog: pytest.LogCaptureFixture
# ):
#     @add_nx_class_basemodel
#     class NxData(NxGroup):
#         data: NxObject  # A NXdata should contain a single field for `data:`
#
#     @NexusDevices.add_device_from_pydantic_schema(
#         NxData(data=NxObject(some_data_key=NxField(data_key="user_readback")))
#     )
#     class SomeSimMotor(SimMotor): ...
#
#     RE_directly_subscribed(bp.count([SomeSimMotor(name="sim_motor")]))
#


def test_nx_data_multi_dimensional(RE_directly_subscribed: RunEngine, tmpdir: Path):
    @NexusDevices.add_device_from_schema(
        {
            "$nxclass": "NXdata",
            "$axes": ["axis1", "axis2"],
            "$signal": "data",
            "data": "data",
            "axis1": "axis1",
            "axis2": "axis2",
        }
    )
    class MultiAxisDataDetector(StandardReadable):
        def __init__(self, name: str = ""):
            super().__init__(name=name)
            with self.add_children_as_readables():
                self.data, self._setter = soft_signal_r_and_setter(float)
                self.axis1 = soft_signal_rw(float)
                self.axis2 = soft_signal_rw(float)
                self.another_signal, _ = soft_signal_r_and_setter(int)

        async def _new_value(self, *args, **kwargs):
            self._setter(sin(await self.axis1.get_value()) * sin(await self.axis2.get_value()))

        async def connect(self, *args, **kawrgs):
            await super().connect(mock=True)
            callback_on_mock_put(self.axis1, self._new_value)
            callback_on_mock_put(self.axis2, self._new_value)

    detector = MultiAxisDataDetector(name="some_detector")
    RE_directly_subscribed(ensure_connected(detector))
    RE_directly_subscribed(
        bp.scan_nd(
            [detector],
            cycler(detector.axis1, range(5)) * cycler(detector.axis2, range(10)),
        )
    )
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == ["some_detector"]
    assert list(loaded["some_detector"]) == [
        "another_signal",
        "axis1",
        "axis2",
        "data",
    ]
    assert set(loaded["some_detector"].attrs) == {"axes", "nxclass", "signal"}
    assert loaded["some_detector"].attrs["nxclass"] == "NXdata"
    assert loaded["some_detector"].attrs["signal"] == "data"
    assert loaded["some_detector"].attrs["axes"] == ["axis1", "axis2"]


def test_timestamps_of_data_key(RE_directly_subscribed: RunEngine, tmpdir: Path):
    read_times = []

    @NexusDevices.add_device_from_schema(
        {
            "$nxclass": "NXdata",
            "$axes": ["signal1_t"],
            "$signal": "signal1",
            "signal1": "signal1",
            "signal1_t": {"timestamps_of_data_key": "signal1"},
            "signal2": "signal1",
            "signal4_t": {"timestamps_of_data_key": "signal4"},
        },
        inherit=False,
    )
    class SomeDetector(StandardReadable):
        def __init__(self, name: str = "") -> None:
            super().__init__(name)
            with self.add_children_as_readables():
                self.signal1, self._s1 = soft_signal_r_and_setter(int)
                self.signal2, self._s2 = soft_signal_r_and_setter(int)
                self.signal3, self._s3 = soft_signal_r_and_setter(int)
                self.signal4, self._s4 = soft_signal_r_and_setter(int)

        async def read(self):
            for f in (self._s1, self._s2, self._s3, self._s4):
                f(0)  # update the value for a new timestamp

            read_times.append(time())
            return await super().read()

    RE_directly_subscribed(bp.count([SomeDetector(name="some_detector")], num=4))
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]["some_detector"]
    assert list(loaded) == [
        "signal1",
        "signal1_t",
        "signal2",
        "signal3",
        "signal4",
        "signal4_t",
    ]

    assert len(loaded["signal1_t"]) == 4
    timestamps = [float(f) for f in loaded["signal1_t"]]

    assert all(timestamps[i] - timestamps[i - 1] > 0 for i in range(1, len(timestamps)))
    assert all(t >= 0 for t in timestamps)
    read_times = np.array(read_times) - read_times[0]

    assert np.allclose(np.array(loaded["signal1_t"]), read_times, atol=0.01, rtol=0)
    assert loaded["signal1_t"].attrs["units"] == "s"
    assert loaded["signal4_t"].attrs["units"] == "s"
