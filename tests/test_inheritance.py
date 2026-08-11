from pathlib import Path

from bluesky import RunEngine
from bluesky import plans as bp
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd.sim import SynAxis
from ophyd_async.core import StandardReadableFormat as Fmt
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor
from ophyd_async.plan_stubs import ensure_connected

from bluesky_nexus import NexusDevice
from bluesky_nexus.nx_schema.nx_base import NxBase

from . import load_only_generated_nexus_file


def test_schema_single_inheritance():
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "the_odysee": {
                "@nxclass": "NXfield",
                "@units": "lyrics",
                "data_key": "signal_made_of_bronze",
            },
        }
    )
    class Grandma(Device):
        signal_made_of_bronze = Cpt(EpicsSignal, "BRONZE")

    expected_grandma_schema = {
        "the_odysee": {
            "data_key": "signal_made_of_bronze",
            "nx_alias": "the_odysee",
            "@nxclass": "NXfield",
            "@units": "lyrics",
        }
    }

    assert (
        Grandma("GRANDMA", name="granma").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "@nxclass": "NXobject",
                **expected_grandma_schema,
            }
        ).model_dump()
    )

    @NexusDevice.from_dictionary(
        {"@nxclass": "NXobject", "beowulf": "signal_made_of_iron"}
    )
    class Mama(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    expected_mama_schema = {
        "beowulf": {
            "data_key": "signal_made_of_iron",
            "nx_alias": "beowulf",
            "@nxclass": "NXfield",
        },
    }
    expected_mama_schema.update(expected_grandma_schema)

    assert (
        Mama("MAMA", name="mama").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "@nxclass": "NXobject",
                **expected_mama_schema,
            }
        ).model_dump()
    )

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "pride_and_prejudice": "signal_made_of_steel",
            "the_odysee": {
                "@nxclass": "NXobject",
                "new_movie": "signal_made_of_bronze",
            },
        }
    )
    class Me(Mama):
        signal_made_of_steel = Cpt(EpicsSignal, "STEEL")

    expected_me_schema = {
        "pride_and_prejudice": {
            "data_key": "signal_made_of_steel",
            "nx_alias": "pride_and_prejudice",
            "@nxclass": "NXfield",
        },
    }
    expected_me_schema.update(expected_mama_schema)
    expected_me_schema["the_odysee"] = {  # type: ignore
        "@nxclass": "NXobject",
        "new_movie": {  # We can override fields from the parent
            "@nxclass": "NXfield",
            "data_key": "signal_made_of_bronze",
            "nx_alias": "new_movie",
        },
    }

    assert (
        Me("ME", name="me").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "@nxclass": "NXobject",
                **expected_me_schema,
            }
        ).model_dump()
    )

    expected_auntie_schema = {
        "@nxclass": "NXobject",
        "beowulf": {
            "data_key": "signal_made_of_iron",
            "nx_alias": "beowulf",
            "@nxclass": "NXfield",
        },
    }

    @NexusDevice.from_dictionary(
        {"@nxclass": "NXobject", "beowulf": "signal_made_of_iron"}, inherit=False
    )
    class Auntie(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    assert Auntie("AUNTIE", name="auntie").hints["NX_schema"] == expected_auntie_schema

    expected_me_schema = {
        "@nxclass": "NXobject",
        "pride_and_prejudice": {
            "data_key": "signal_made_of_steel",
            "nx_alias": "pride_and_prejudice",
            "@nxclass": "NXfield",
        },
    }
    expected_me_schema.update(expected_auntie_schema)

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "pride_and_prejudice": "signal_made_of_steel",
        }
    )
    class ITakeOnlyAfterMyAunt(Auntie):
        signal_made_of_steel = Cpt(EpicsSignal, "STEEL")

    assert (
        ITakeOnlyAfterMyAunt("ME", name="me").hints["NX_schema"] == expected_me_schema
    )


def test_schema_multi_inheritance():
    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signalnm": "value11",
            "signal1n": "value11",
            "signaln1": "value11",
            "GROUP": {
                "@nxclass": "NXobject",
                "signalnm": "value11",
                "signal1n": "value11",
                "signaln1": "value11",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrnm": "value11",
                    "@attr1n": "value11",
                    "@attrn1": "value11",
                },
            },
        },
    )
    class Device11(Device):
        device_n_m_int = 11
        device_1_n_int = 11
        device_n_1_int = 11

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signalnm": "value12",
            "signal1n": "value12",
            "signaln2": "value12",
            "GROUP": {
                "@nxclass": "NXobject",
                "signalnm": "value12",
                "signal1n": "value12",
                "signaln2": "value12",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrnm": "value12",
                    "@attr1n": "value12",
                    "@attrn2": "value12",
                },
            },
        },
    )
    class Device12(Device):
        device_n_m_int = 12
        device_1_n_int = 12
        device_n_2_int = 12

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signaln": "value1",
            "signal1": "value1",
            "GROUP": {
                "@nxclass": "NXobject",
                "signaln": "value1",
                "signal1": "value1",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrn": "value1",
                    "@attr1": "value1",
                },
            },
        },
    )
    class Device1(Device11, Device12):
        device_n_int = 1
        device_1_int = 1

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signalnm": "value21",
            "signal2n": "value21",
            "signaln1": "value21",
            "GROUP": {
                "@nxclass": "NXobject",
                "signalnm": "value21",
                "signal2n": "value21",
                "signaln1": "value21",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrnm": "value21",
                    "@attr2n": "value21",
                    "@attrn1": "value21",
                },
            },
        },
    )
    class Device21(Device):
        device_n_m_int = 21
        device_2_n_int = 21
        device_n_1_int = 21

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signalnm": "value22",
            "signal2n": "value22",
            "signaln2": "value22",
            "GROUP": {
                "@nxclass": "NXobject",
                "signalnm": "value22",
                "signal2n": "value22",
                "signaln2": "value22",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrnm": "value22",
                    "@attr2n": "value22",
                    "@attrn2": "value22",
                },
            },
        },
    )
    class Device22(Device):
        device_n_m_int = 22
        device_2_n_int = 22
        device_n_2_int = 22

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXobject",
            "signaln": "value2",
            "signal2": "value2",
            "GROUP": {
                "@nxclass": "NXobject",
                "signaln": "value2",
                "signal2": "value2",
                "signal": {
                    "@nxclass": "NXfield",
                    "data_key": "signal",
                    "@attrn": "value2",
                    "@attr2": "value2",
                },
            },
        },
    )
    class Device2(Device21, Device22):
        device_n_int = 2
        device_2_int = 2

    class InheritedButNotWrapped(Device1, Device2): ...

    device = InheritedButNotWrapped("P", name="device")
    assert device.device_2_int == 2
    assert device.device_1_int == 1
    assert device.device_n_int == 1  # Prefers left

    assert device.device_n_m_int == 11  # Prefers left all the way up

    # Prefers left on this level
    assert device.device_1_n_int == 11
    assert device.device_2_n_int == 21
    assert device.device_n_1_int == 11
    assert device.device_n_2_int == 12

    # The schema follows the same behaviour with overriding...
    assert device.hints["NX_schema"] == {
        "GROUP": {
            "@nxclass": "NXobject",
            "signal": {
                "@attr1": {
                    "constant": "value1",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attr1",
                },
                "@attr1n": {
                    "constant": "value11",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attr1n",
                },
                "@attr2": {
                    "constant": "value2",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attr2",
                },
                "@attr2n": {
                    "constant": "value21",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attr2n",
                },
                "@attrn": {
                    "constant": "value1",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attrn",
                },
                "@attrn1": {
                    "constant": "value11",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attrn1",
                },
                "@attrn2": {
                    "constant": "value12",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attrn2",
                },
                "@attrnm": {
                    "constant": "value11",
                    "data_key": None,
                    "hints_key": None,
                    "name": "@attrnm",
                },
                "data_key": "signal",
                "nx_alias": "signal",
                "@nxclass": "NXfield",
            },
            "signal1": {
                "data_key": "value1",
                "nx_alias": "signal1",
                "@nxclass": "NXfield",
            },
            "signal1n": {
                "data_key": "value11",
                "nx_alias": "signal1n",
                "@nxclass": "NXfield",
            },
            "signal2": {
                "data_key": "value2",
                "nx_alias": "signal2",
                "@nxclass": "NXfield",
            },
            "signal2n": {
                "data_key": "value21",
                "nx_alias": "signal2n",
                "@nxclass": "NXfield",
            },
            "signaln": {
                "data_key": "value1",
                "nx_alias": "signaln",
                "@nxclass": "NXfield",
            },
            "signaln1": {
                "data_key": "value11",
                "nx_alias": "signaln1",
                "@nxclass": "NXfield",
            },
            "signaln2": {
                "data_key": "value12",
                "nx_alias": "signaln2",
                "@nxclass": "NXfield",
            },
            "signalnm": {
                "data_key": "value11",
                "nx_alias": "signalnm",
                "@nxclass": "NXfield",
            },
        },
        "@nxclass": "NXobject",
        "signal1": {"data_key": "value1", "nx_alias": "signal1", "@nxclass": "NXfield"},
        "signal1n": {
            "data_key": "value11",
            "nx_alias": "signal1n",
            "@nxclass": "NXfield",
        },
        "signal2": {"data_key": "value2", "nx_alias": "signal2", "@nxclass": "NXfield"},
        "signal2n": {
            "data_key": "value21",
            "nx_alias": "signal2n",
            "@nxclass": "NXfield",
        },
        "signaln": {"data_key": "value1", "nx_alias": "signaln", "@nxclass": "NXfield"},
        "signaln1": {
            "data_key": "value11",
            "nx_alias": "signaln1",
            "@nxclass": "NXfield",
        },
        "signaln2": {
            "data_key": "value12",
            "nx_alias": "signaln2",
            "@nxclass": "NXfield",
        },
        "signalnm": {
            "data_key": "value11",
            "nx_alias": "signalnm",
            "@nxclass": "NXfield",
        },
    }


def test_schema_single_inheritance_on_device(
    RE_directly_subscribed: RunEngine, tmpdir: Path
):
    NexusDevice.from_dictionary(
        {
            "@nxclass": "NXpositioner",
            "value": "",
            "target_value": "user_setpoint",
            "tolerance": "encoder_resolution",
            "soft_limit_min": "low_limit_travel",
            "soft_limit_max": "high_limit_travel",
            "velocity": "velocity",
            "acceleration_time": "acceleration_time",
        }
    )(Motor)

    class Shutter(Motor):
        def __init__(self, prefix: str, name: str = ""):
            super().__init__(prefix, name=name)
            with self.add_children_as_readables(format=Fmt.CONFIG_SIGNAL):
                self.open_value = epics_signal_r(float, f"{prefix}:OPEN_VAL")
                self.close_value = epics_signal_r(float, f"{prefix}:CLOSE_VAL")

    @NexusDevice.from_dictionary(
        {
            "@nxclass": "NXpositioner",
            "SUB_GROUP": {"@nxclass": "NXobject", "value_at_open": "open_value"},
        }
    )
    class ShutterWithSomeDifferingNxSchema(Shutter): ...

    shutter_with_some_differing_schema = ShutterWithSomeDifferingNxSchema(
        "S1", name="shutter_differing"
    )
    shutter = Shutter("S2", name="shutter")
    # assert shutter.hints == shutter_with_some_differing_schema.hints

    RE_directly_subscribed(
        ensure_connected(shutter_with_some_differing_schema, shutter, mock=True)
    )
    RE_directly_subscribed(
        bp.count([shutter, shutter_with_some_differing_schema], num=3)
    )  # type: ignore

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]
    assert list(loaded) == ["shutter", "shutter_differing", "time"]
    assert list(loaded["shutter"]) == [
        "close_value",
        "motor_egu",
        "motor_resolution",
        "offset",
        "open_value",
        "steps_per_revolution",
        "tolerance",
        "units_per_revolution",
        "value",
        "velocity",
    ]
    assert list(loaded["shutter_differing"]) == [
        "SUB_GROUP",
        "close_value",
        "motor_egu",
        "motor_resolution",
        "offset",
        "steps_per_revolution",
        "tolerance",
        "units_per_revolution",
        "value",
        "velocity",
    ]
    assert list(loaded["shutter_differing"]["SUB_GROUP"]) == ["value_at_open"]


def test_description_accross_whole_codebase(
    RE_directly_subscribed: RuntimeError, tmpdir: Path, monkeypatch
):
    # Makeing a new class only to avoid persistence problems in pytest
    # (monkeypatch is annoying here). This test demonstrates that if I
    # were to have added description to device in a centralized
    # device package, I wouldn't have to add the description to any
    # other devices read.
    @NexusDevice.from_dictionary(
        {"@nxclass": "NXgroup", "@description": {"hints_key": ["md", "description"]}}
    )
    class ThisWouldBeTheRealDeviceInThePackage(Device): ...

    class SynAxisWouldUseTheAbove(ThisWouldBeTheRealDeviceInThePackage, SynAxis): ...

    description = (
        "This description was added from the patch to ophyd device. "
        "We can have it in all devices accross the codebase for free."
    )

    device = SynAxisWouldUseTheAbove(name="device")  # type: ignore
    device.md = {"description": description}

    RE_directly_subscribed(bp.count([device], num=3))  # type: ignore

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"][
        "device"
    ]
    assert list(loaded.attrs) == ["description", "nxclass"]
    assert loaded.attrs["description"] == description
