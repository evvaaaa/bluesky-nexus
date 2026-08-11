from pathlib import Path

from bluesky import RunEngine
from bluesky import plans as bp
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
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
            "nx_class": "NXobject",
            "the_odysee": {
                "nx_class": "NXfield",
                "@units": "lyrics",
                "datakey": "signal_made_of_bronze",
            },
        }
    )
    class Grandma(Device):
        signal_made_of_bronze = Cpt(EpicsSignal, "BRONZE")

    expected_grandma_schema = {
        "the_odysee": {
            "datakey": "signal_made_of_bronze",
            "nx_alias": "the_odysee",
            "nx_class": "NXfield",
            "@units": "lyrics",
        }
    }

    assert (
        Grandma("GRANDMA", name="granma").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "nx_class": "NXobject",
                **expected_grandma_schema,
            }
        ).model_dump()
    )

    @NexusDevice.from_dictionary(
        {"nx_class": "NXobject", "beowulf": "signal_made_of_iron"}
    )
    class Mama(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    expected_mama_schema = {
        "beowulf": {
            "datakey": "signal_made_of_iron",
            "nx_alias": "beowulf",
            "nx_class": "NXfield",
        },
    }
    expected_mama_schema.update(expected_grandma_schema)

    assert (
        Mama("MAMA", name="mama").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "nx_class": "NXobject",
                **expected_mama_schema,
            }
        ).model_dump()
    )

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "pride_and_prejudice": "signal_made_of_steel",
            "the_odysee": {
                "nx_class": "NXobject",
                "new_movie": "signal_made_of_bronze",
            },
        }
    )
    class Me(Mama):
        signal_made_of_steel = Cpt(EpicsSignal, "STEEL")

    expected_me_schema = {
        "pride_and_prejudice": {
            "datakey": "signal_made_of_steel",
            "nx_alias": "pride_and_prejudice",
            "nx_class": "NXfield",
        },
    }
    expected_me_schema.update(expected_mama_schema)
    expected_me_schema["the_odysee"] = {
        "nx_class": "NXobject",
        "new_movie": {  # We can override fields from the parent
            "nx_class": "NXfield",
            "datakey": "signal_made_of_bronze",
            "nx_alias": "new_movie",
        },
    }

    assert (
        Me("ME", name="me").hints["NX_schema"]
        == NxBase.from_dict(
            {
                "nx_class": "NXobject",
                **expected_me_schema,
            }
        ).model_dump()
    )

    expected_auntie_schema = {
        "nx_class": "NXobject",
        "beowulf": {
            "datakey": "signal_made_of_iron",
            "nx_alias": "beowulf",
            "nx_class": "NXfield",
        },
    }

    @NexusDevice.from_dictionary(
        {"nx_class": "NXobject", "beowulf": "signal_made_of_iron"}, inherit=False
    )
    class Auntie(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    assert Auntie("AUNTIE", name="auntie").hints["NX_schema"] == expected_auntie_schema

    expected_me_schema = {
        "nx_class": "NXobject",
        "pride_and_prejudice": {
            "datakey": "signal_made_of_steel",
            "nx_alias": "pride_and_prejudice",
            "nx_class": "NXfield",
        },
    }
    expected_me_schema.update(expected_auntie_schema)

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
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
            "nx_class": "NXobject",
            "grandma_on_dads_side_signal": None,
            "override_group_on_dads_side": {
                "nx_class": "NXobject",
                "signal_dad_grandma": None,
                "signal_from_grandma": None,
            },
        },
    )
    class GrandmaOnDadsSide(Device):
        grandparent_int = 0

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "granddad_on_dads_side_signal": None,
            "override_group_on_dads_side": {
                "nx_class": "NXobject",
                "signal_dad_granddad": None,
            },
        }
    )
    class GranddadOnDadsSide(Device):
        grandparent_int = 1

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "dad_signal": None,
        }
    )
    class Dad(GrandmaOnDadsSide, GranddadOnDadsSide):
        direct_parent_int = 0

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "grandma_on_mums_side_signal": None,
            "override_group_on_mums_side": {
                "nx_class": "NXobject",
                "signal_mum_grandma": None,
                "@units": "from grandma",
            },
        }
    )
    class GrandmaOnMumsSide(Device):
        grandparent_int = 2

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "granddad_on_mums_side_signal": None,
            "override_group_on_mums_side": {
                "nx_class": "NXobject",
                "signal_mum_grandad": None,
            },
        }
    )
    class GranddadOnMumsSide(Device):
        grandparent_int = 3

    @NexusDevice.from_dictionary(
        {"nx_class": "NXgroup", "mum_signal": None}, inherit=False
    )
    class Mum(GrandmaOnMumsSide, GranddadOnMumsSide):
        direct_parent_int = 1

    class Me(Dad, Mum): ...

    me = Me("ME", name="me")

    assert me.grandparent_int == 0

    # Inheritence treats left as more important in the mro.
    # So do we.
    assert me.direct_parent_int == 0
    assert me.hints["NX_schema"] == {
        "dad_signal": {
            "datakey": "dad_signal",
            "nx_alias": "dad_signal",
            "nx_class": "NXfield",
        },
        "granddad_on_dads_side_signal": {
            "datakey": "granddad_on_dads_side_signal",
            "nx_alias": "granddad_on_dads_side_signal",
            "nx_class": "NXfield",
        },
        "grandma_on_dads_side_signal": {
            "datakey": "grandma_on_dads_side_signal",
            "nx_alias": "grandma_on_dads_side_signal",
            "nx_class": "NXfield",
        },
        "mum_signal": {
            "datakey": "mum_signal",
            "nx_alias": "mum_signal",
            "nx_class": "NXfield",
        },
        "nx_class": "NXobject",
        "override_group_on_dads_side": {
            "nx_class": "NXobject",
            "signal_dad_granddad": {
                "datakey": "signal_dad_granddad",
                "nx_alias": "signal_dad_granddad",
                "nx_class": "NXfield",
            },
            "signal_dad_grandma": {
                "datakey": "signal_dad_grandma",
                "nx_alias": "signal_dad_grandma",
                "nx_class": "NXfield",
            },
            "signal_from_grandma": {
                "datakey": "signal_from_grandma",
                "nx_alias": "signal_from_grandma",
                "nx_class": "NXfield",
            },
        },
    }


def test_schema_single_inheritance_on_device(
    RE_directly_subscribed: RunEngine, tmpdir: Path
):
    NexusDevice.from_dictionary(
        {
            "nx_class": "NXpositioner",
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
            "SUB_GROUP": {"nx_class": "NXobject", "value_at_open": "open_value"},
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
