"""Tests with different kinds of plan.

"simple" reads/one shots on standard readables are well enough tested in other files.

This tests for e.g, flyers where events are collected, flyers where external asset
documents are generated, event_pages are made, a devices configuration is provided
twice etc.
"""

from pathlib import Path

from bluesky import RunEngine
from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from ophyd.sim import SynAxis

from . import load_only_generated_nexus_file


def test_descriptor_reconfiguration(RE_directly_subscribed: RunEngine, tmpdir: Path) -> None:
    motor = SynAxis(name="motor")

    def plan() -> MsgGenerator:
        yield from bps.open_run()
        yield from bps.one_shot([motor])  # type: ignore
        yield from bps.declare_stream(motor, name="primary")  # type: ignore
        yield from bps.one_shot([motor])  # type: ignore
        yield from bps.one_shot([motor])  # type: ignore
        yield from bps.close_run()

    RE_directly_subscribed(plan())
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["streams"]["primary"]["devices"][
        "motor"
    ]
    assert list(loaded) == [
        "acceleration",
        "motor",
        "setpoint",
        "velocity",
    ]

    assert "motor_velocity" in motor.describe_configuration()
    assert "motor_setpoint" in motor.describe()
    assert list(loaded["velocity"]["value"]) == [1, 1]
    assert list(loaded["motor"]["value"]) == [0, 0, 0]
