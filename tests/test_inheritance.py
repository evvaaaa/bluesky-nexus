from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from bluesky_nexus import NexusDevice


def test_schema_single_inheritance():
    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "the_odysee": {
                "nx_class": "NXfield",
                "nx_units": "lyrics",
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
            "nx_units": "lyrics",
        }
    }

    assert Grandma("GRANDMA", name="granma").hints["NX_schema"] == {
        "nx_class": "NXobject",
        **expected_grandma_schema,
    }

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
            "nx_units": None,
        },
    }
    expected_mama_schema.update(expected_grandma_schema)

    assert Mama("MAMA", name="mama").hints["NX_schema"] == {
        "nx_class": "NXobject",
        **expected_mama_schema,
    }

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
            "nx_units": None,
        },
    }
    expected_me_schema.update(expected_mama_schema)
    expected_me_schema["the_odysee"] = {
        "nx_class": "NXobject",
        "new_movie": {  # We can override fields from the parent
            "nx_class": "NXfield",
            "nx_units": None,
            "datakey": "signal_made_of_bronze",
            "nx_alias": "new_movie",
        },
    }

    assert Me("ME", name="me").hints["NX_schema"] == {
        "nx_class": "NXobject",
        **expected_me_schema,
    }

    expected_auntie_schema = {
        "nx_class": "NXobject",
        "beowulf": {
            "datakey": "signal_made_of_iron",
            "nx_alias": "beowulf",
            "nx_class": "NXfield",
            "nx_units": None,
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
            "nx_units": None,
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
                "nx_units": "from grandma",
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
                "nx_units": "from grandma",
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
    # so do we.
    assert me.direct_parent_int == 0

    assert me.hints["NX_schema"] == {
        "dad_signal": {
            "datakey": "dad_signal",
            "nx_alias": "dad_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "granddad_on_dads_side_signal": {
            "datakey": "granddad_on_dads_side_signal",
            "nx_alias": "granddad_on_dads_side_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "grandma_on_dads_side_signal": {
            "datakey": "grandma_on_dads_side_signal",
            "nx_alias": "grandma_on_dads_side_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "mum_signal": {
            "datakey": "mum_signal",
            "nx_alias": "mum_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "nx_class": "NXobject",
        "override_group_on_dads_side": {
            "nx_class": "NXobject",
            "nx_units": "from grandma",
            "signal_dad_grandma": {
                "datakey": "signal_dad_grandma",
                "nx_alias": "signal_dad_grandma",
                "nx_class": "NXfield",
                "nx_units": None,
            },
        },
    }
