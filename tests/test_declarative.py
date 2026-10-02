from pathlib import Path
from typing import Annotated as A

from bluesky import RunEngine, plans
from ophyd_async.core import SignalR, SignalRW, StandardReadable
from ophyd_async.core import StandardReadableFormat as Fmt
from ophyd_async.epics.core import EpicsDevice, PvSuffix
from ophyd_async.plan_stubs import ensure_connected

from bluesky_nexus.device import NxConstant, NxDataKey, NxDevice
from bluesky_nexus.schema.nx_base_class import NxBaseClass

from . import load_only_generated_nexus_file


def test_device_datakeys_map():
    # class ProceduralNxDeclarativeSignals(NxDevice, StandardReadable, EpicsDevice):
    #     BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")(
    #         data=NxField(data_key="signal_2"),
    #         diameter=NxField(data_key="signal_3"),
    #         description=NxField(constant="This sure is a detector."),
    #     )
    #
    #     signal_1: A[SignalR[float], PvSuffix("1"), Fmt.CONFIG_SIGNAL]
    #     signal_2: A[SignalR[float], PvSuffix("2"), Fmt.CHILD]
    #
    #     signal_3: A[SignalRW[float], PvSuffix("3"), NxDataKey("data"), Fmt.CHILD]
    #     signal_4: A[SignalRW[float], PvSuffix("4"), NxDataKey("diameter"), Fmt.CONFIG_SIGNAL]
    #
    # class DeclarativeNxDeclarativeSignals(NxDevice, StandardReadable, EpicsDevice):
    #     BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")
    #
    #     signal_1: A[SignalR[float], PvSuffix("1"), Fmt.CONFIG_SIGNAL]
    #     signal_2: A[SignalR[float], PvSuffix("2"), Fmt.CHILD]
    #
    #     signal_3: A[SignalRW[float], PvSuffix("3"), NxDataKey("data"), Fmt.CHILD]
    #     signal_4: A[SignalRW[float], PvSuffix("4"), NxDataKey("diameter"), Fmt.CONFIG_SIGNAL]
    #
    #     some_variable_on_this_class: A[str, NxConstant("description")] = (
    #         "This is a fancy declarative child detector."
    #     )
    #
    class Device(NxDevice, StandardReadable, EpicsDevice):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")

        signal_1: A[SignalR[float], PvSuffix("1"), Fmt.CONFIG_SIGNAL]
        signal_2: A[SignalR[float], PvSuffix("2"), Fmt.CHILD]

        signal_3: A[SignalRW[float], PvSuffix("3"), NxDataKey("data"), Fmt.CHILD]
        signal_4: A[SignalRW[float], PvSuffix("4"), NxDataKey("diameter"), Fmt.CONFIG_SIGNAL]

        some_variable_on_this_class: A[str, NxConstant("description")] = (
            "This is a fancy parent detector."
        )
        signal_5: A[
            SignalRW[str],
            PvSuffix("5"),
            NxDataKey("my_silly_attribute", is_nx_attribute=True),
            Fmt.CONFIG_SIGNAL,
        ]

    assert Device("PREFIX:", name="det").hints == {
        "NX_class": "NXdetector",
        "NX_schema": {
            "description": {"constant": "This is a fancy parent detector."},
            "data": "signal_3",
            "diameter": "signal_4",
            "$my_silly_attribute": {"data_key": "signal_5"},
            "$nxclass": "NXdetector",
        },
    }


def test_constants_defined_by_python_variables_not_provided_on_class(
    RE_directly_subscribed: RunEngine, tmpdir: Path
):
    class Device(NxDevice, StandardReadable, EpicsDevice):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")
        signal: A[SignalRW[int], PvSuffix("SIGNAL"), NxDataKey("data"), Fmt.CHILD]
        a: A[str, NxConstant("a_map")]
        b: A[str, NxConstant("b_map")]

        def __init__(self, prefix: str = "", name: str = "") -> None:
            super().__init__(prefix=prefix, name=name)
            self.a = "a value"

    device = Device("PREFIX", name="device")
    RE_directly_subscribed(ensure_connected(device, mock=True))
    RE_directly_subscribed(plans.count([device], num=3))
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == ["device"]
    assert list(loaded["device"]) == ["a_map", "data"]
    assert loaded["device"]["a_map"] == "a value"


def test_inherited_declarative_definitions():
    class Parent(NxDevice, StandardReadable, EpicsDevice):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")

        signal_1: A[SignalR[float], PvSuffix("1"), Fmt.CONFIG_SIGNAL]
        signal_2: A[SignalR[float], PvSuffix("2"), Fmt.CHILD]

        signal_3: A[SignalRW[float], PvSuffix("3"), NxDataKey("data"), Fmt.CHILD]
        signal_4: A[SignalRW[float], PvSuffix("4"), NxDataKey("diameter"), Fmt.CONFIG_SIGNAL]

        some_variable_on_this_class: A[str, NxConstant("description")] = (
            "This is a fancy parent detector."
        )

    class Child(Parent, StandardReadable, EpicsDevice):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.build("NXdetector")

        signal_5: A[SignalRW[float], PvSuffix("4"), NxDataKey("width"), Fmt.CONFIG_SIGNAL]

        some_variable_on_this_class: A[str, NxConstant("description")] = (
            "This is a fancy child detector."
        )

    assert Child(prefix="PREFIX:", name="det").hints == {
        "NX_class": "NXdetector",
        "NX_schema": {
            "description": {"constant": "This is a fancy child detector."},
            "data": "signal_3",
            "diameter": "signal_4",
            "width": "signal_5",
            "$nxclass": "NXdetector",
        },
    }
