"""These tests are for how the schema is parsed/created in the writer."""

import re
from pathlib import Path

import pytest
from bluesky import RunEngine
from bluesky import plans as bp
from nexusformat import nexus
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal
from ophyd_async.core import StandardReadable, StandardReadableFormat, soft_signal_rw
from ophyd_async.sim import SimMotor, SimPointDetector

from bluesky_nexus import NexusDevice
from bluesky_nexus.nx_schema import NxField, NxGroup, add_nx_class_basemodel

from . import get_logs, load_only_generated_nexus_file, wait_for_nexus_file


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


def test_schema_client_server_differing_schema(
    RE_subscribed_over_zmq: RunEngine, tmpdir: Path
):
    new_motor_schema = {"nx_class": "NXnew", "some_data": "<name>-foo"}

    with pytest.raises(
        TypeError,
        match=(
            "Requested `nx_class: NXnew` but this isn't defined with pydantic schemas:"
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
    loaded = wait_for_nexus_file(tmpdir)
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
    assert str(loaded["entry"]["primary"]["motor"].attrs["nxclass"]) == nexus.NXattr(
        "NXobject"
    )
    assert list(loaded["entry"]["primary"]["motor"]) == [
        "acceleration_time",
        "motor",
        "velocity",
    ]
    assert list(loaded["entry"]["primary"]["motor"]["motor"]) == [0, 0, 0]


def test_schema_single_inheritance():
    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "the_odysee": {
                "nx_class": "NXfield",
                "nx_units": "lyrics",
                "datakey": "<name>-signal_made_of_bronze",
            },
        }
    )
    class Grandma(Device):
        signal_made_of_bronze = Cpt(EpicsSignal, "BRONZE")

    expected_grandma_schema = {
        "the_odysee": {
            "datakey": "<name>-signal_made_of_bronze",
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
        {"nx_class": "NXobject", "beowulf": "<name>-signal_made_of_iron"}
    )
    class Mama(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    expected_mama_schema = {
        "beowulf": {
            "datakey": "<name>-signal_made_of_iron",
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
            "pride_and_prejudice": "<name>-signal_made_of_steel",
            "the_odysee": {
                "nx_class": "NXobject",
                "new_movie": "<name>-signal_made_of_bronze",
            },
        }
    )
    class Me(Mama):
        signal_made_of_steel = Cpt(EpicsSignal, "STEEL")

    expected_me_schema = {
        "pride_and_prejudice": {
            "datakey": "<name>-signal_made_of_steel",
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
            "datakey": "<name>-signal_made_of_bronze",
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
            "datakey": "<name>-signal_made_of_iron",
            "nx_alias": "beowulf",
            "nx_class": "NXfield",
            "nx_units": None,
        },
    }

    @NexusDevice.from_dictionary(
        {"nx_class": "NXobject", "beowulf": "<name>-signal_made_of_iron"}, inherit=False
    )
    class Auntie(Grandma):
        signal_made_of_iron = Cpt(EpicsSignal, "IRON")

    assert Auntie("AUNTIE", name="auntie").hints["NX_schema"] == expected_auntie_schema

    expected_me_schema = {
        "nx_class": "NXobject",
        "pride_and_prejudice": {
            "datakey": "<name>-signal_made_of_steel",
            "nx_alias": "pride_and_prejudice",
            "nx_class": "NXfield",
            "nx_units": None,
        },
    }
    expected_me_schema.update(expected_auntie_schema)

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "pride_and_prejudice": "<name>-signal_made_of_steel",
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
            "<name>_grandma_on_dads_side_signal": None,
            "override_group_on_dads_side": {
                "nx_class": "NXobject",
                "<name>_signal_dad_grandma": None,
                "nx_units": "from grandma",
            },
        },
    )
    class GrandmaOnDadsSide(Device):
        grandparent_signal = 0

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>_granddad_on_dads_side_signal": None,
            "override_group_on_dads_side": {
                "nx_class": "NXobject",
                "<name>_signal_dad_granddad": None,
            },
        }
    )
    class GranddadOnDadsSide(Device):
        grandparent_signal = 1

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>_dad_signal": None,
        }
    )
    class Dad(GrandmaOnDadsSide, GranddadOnDadsSide):
        direct_parent_int = 0

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>-grandma_on_mums_side_signal": None,
            "override_group_on_mums_side": {
                "nx_class": "NXobject",
                "<name>_signal_mum_grandma": None,
                "nx_units": "from grandma",
            },
        }
    )
    class GrandmaOnMumsSide(Device):
        grandparent_signal = 2

    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>-granddad_on_mums_side_signal": None,
            "override_group_on_mums_side": {
                "nx_class": "NXobject",
                "<name>_signal_mum_grandad": None,
            },
        }
    )
    class GranddadOnMumsSide(Device):
        grandparent_signal = 3

    @NexusDevice.from_dictionary(
        {"nx_class": "NXgroup", "<name>-mum_signal": None}, inherit=False
    )
    class Mum(GrandmaOnMumsSide, GranddadOnMumsSide):
        direct_parent_int = 1

    class Me(Dad, Mum): ...

    me = Me("ME", name="me")

    assert me.grandparent_signal == 0

    # Inheritence treads left as more important
    # so do we.
    assert me.direct_parent_int == 0

    assert me.hints["NX_schema"] == {
        "dad_signal": {
            "datakey": "<name>_dad_signal",
            "nx_alias": "dad_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "granddad_on_dads_side_signal": {
            "datakey": "<name>_granddad_on_dads_side_signal",
            "nx_alias": "granddad_on_dads_side_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "grandma_on_dads_side_signal": {
            "datakey": "<name>_grandma_on_dads_side_signal",
            "nx_alias": "grandma_on_dads_side_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "mum_signal": {
            "datakey": "<name>-mum_signal",
            "nx_alias": "mum_signal",
            "nx_class": "NXfield",
            "nx_units": None,
        },
        "nx_class": "NXobject",
        "override_group_on_dads_side": {
            "nx_class": "NXobject",
            "nx_units": "from grandma",
            "signal_dad_grandma": {
                "datakey": "<name>_signal_dad_grandma",
                "nx_alias": "signal_dad_grandma",
                "nx_class": "NXfield",
                "nx_units": None,
            },
        },
    }
