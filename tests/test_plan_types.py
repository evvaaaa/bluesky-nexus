"""Tests with different kinds of plan.

"simple" reads/one shots on standard readables are well enough tested in other files.

This tests for e.g, flyers where events are collected, flyers where external asset
documents are generated, event_pages are made, a devices configuration is provided
twice etc.
"""

import time
from collections.abc import AsyncGenerator
from pathlib import Path

from bluesky import RunEngine
from bluesky import plan_stubs as bps
from bluesky.utils import MsgGenerator
from event_model import DataKey, PartialEventPage
from ophyd.sim import SynAxis
from ophyd_async.core import FlyMotorInfo
from ophyd_async.sim import SimMotor

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


def test_collectable_with_event_pages(RE_directly_subscribed: RunEngine, tmpdir: Path) -> None:
    class EventPageCollectable(SimMotor):
        timestamps = {}
        event_times = []

        def __init__(self) -> None:
            super().__init__(name="flyer")

        async def describe_collect(self) -> dict[str, DataKey]:
            return {
                "flyer-signal1": DataKey(dtype="integer", shape=[], source="x"),
                "flyer-signal2": DataKey(dtype="integer", shape=[], source="x"),
            }

        async def collect_pages(self) -> AsyncGenerator[PartialEventPage, None]:
            self.timestamps = {
                "flyer-signal1": [float(time.time()) for _ in range(5)],
                "flyer-signal2": [float(time.time()) for _ in range(5)],
            }
            self.event_times = [time.time() for _ in range(5)]
            yield PartialEventPage(
                timestamps=self.timestamps,
                data={
                    "flyer-signal1": list(range(5)),
                    "flyer-signal2": list(range(5)),
                },
                time=self.event_times,
            )

    flyer = EventPageCollectable()

    def plan() -> MsgGenerator:
        yield from bps.open_run()
        yield from bps.prepare(
            flyer, FlyMotorInfo(start_position=0.0, end_position=1.0, time_for_move=0.1), wait=True
        )
        yield from bps.declare_stream(flyer, name="my-flyer-stream", collect=True)
        yield from bps.kickoff(flyer, wait=True)
        yield from bps.complete(flyer, wait=True)
        yield from bps.collect(flyer, name="my-flyer-stream")
        yield from bps.one_shot([flyer])
        yield from bps.close_run()

    RE_directly_subscribed(plan())
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["streams"]["my_flyer_stream"][
        "devices"
    ]["flyer"]
    for signal in ("flyer-signal1", "flyer-signal2"):
        nx_signal_name = signal.split("-")[-1]

        assert list(loaded[nx_signal_name]["value"]) == list(range(5))
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["streams"]["primary"]["devices"][
        "flyer"
    ]
    assert loaded["flyer"]["value"] == 3.5
