"""
MockFlyer module.

---
--- MockFlyer written by Eva: OP 5811 -> 22.09.2025 09:47 AM
--- All docsstrings added by me (chatgpt generation) to satisfy the pre-commits
---

This module defines a mock implementation of a Bluesky-compatible
`Flyable` device. It can be used for testing workflows that
involve flyer-style devices without requiring actual hardware.

The `MockFlyer` simulates a measurement that starts immediately
(`kickoff`), takes a fixed amount of time (`complete`), and then
produces a synthetic data event (`collect`).
"""

from dataclasses import dataclass
from threading import Thread
from time import sleep, time_ns

from bluesky.protocols import Flyable
from event_model import DataKey, PartialEvent
from ophyd import Device
from ophyd.status import DeviceStatus, Status


@dataclass
class MetadataMockFlyer:
    """Class simulating metadata for a monochromator.

    Attributes:
        description (str): Description of the monochromator.
    """

    description: str = "I am the best flyer"

    def get_attributes(self):
        """Return all metadata attributes of the flayer.

        Returns:
            dict: A dictionary containing all metadata attributes.
        """
        attributes = {
            "description": self.description,
        }
        return attributes


_WAIT_SECONDS = 10.0


class MockFlyer(Device, Flyable):
    """A mock flyer device for testing Bluesky run engines.

    This class simulates the behavior of a flyer device:
    - It starts immediately when `kickoff` is called.
    - It waits asynchronously for a configurable duration
      before completing.
    - It provides a description of its data stream via
      `describe_collect`.
    - It yields synthetic data through `collect`.

    Parameters
    ----------
    *args :
        Positional arguments passed to the `Device` base class.
    wait_seconds : float, optional
        Duration (in seconds) that the flyer should simulate
        measurement time. Defaults to 10.0 seconds.
    **kwargs :
        Additional keyword arguments passed to the `Device`
        base class.
    """

    md = MetadataMockFlyer()

    def __init__(self, *args, wait_seconds: float = _WAIT_SECONDS, **kwargs):
        """Initialize the mock flyer.

        Parameters
        ----------
        *args :
            Positional arguments passed to the `Device` base class.
        wait_seconds : float, optional
            Duration (in seconds) that the flyer should simulate
            measurement time. Defaults to 10.0 seconds.
        **kwargs :
            Additional keyword arguments passed to the `Device`
            base class.
        """
        self.time_start = None
        self._wait_seconds = wait_seconds
        super().__init__(*args, **kwargs)

    def kickoff(self):
        """Start the flyer measurement.

        Records the start time and immediately returns a finished
        `DeviceStatus`, indicating that the flyer has been kicked off.

        Returns
        -------
        DeviceStatus
            A status object marked finished successfully.
        """
        self.time_start = time_ns()
        kickoff_status = DeviceStatus(self)
        kickoff_status._finished(success=True)  # pylint: disable=protected-access
        return kickoff_status

    def complete(self):
        """Wait for the flyer measurement to finish.

        This method returns immediately with a `Status` object,
        and spawns a background thread that marks the status as
        finished once the configured `wait_seconds` has elapsed
        since kickoff.

        Returns
        -------
        Status
            A status object that will be finished asynchronously.
        """
        status = Status()

        def check_time_passed(time_start, status):
            while time_ns() < time_start + self._wait_seconds * 1e9:
                sleep(0.0001)
            status.set_finished()

        Thread(
            target=check_time_passed, args=(self.time_start, status), daemon=True
        ).start()
        return status

    def describe_collect(self):
        """Describe the data stream produced by `collect`.

        Returns metadata in the form of a dictionary mapping
        data keys to `DataKey` objects. Here, a single scalar
        field "time-taken" is advertised.

        Returns
        -------
        dict
            A description of the collected data fields.
        """
        return {
            self.name: {
                "time-taken": DataKey(
                    source="meh",
                    dtype="number",
                    shape=[],
                )
            }
        }

    def collect(self):
        """Yield a synthetic event representing the flyer result.

        The event contains a single field, "time-taken", which
        is the elapsed nanoseconds between kickoff and collection.

        Yields
        ------
        PartialEvent
            A single synthetic event with timing information.
        """
        yield PartialEvent(
            time=time_ns(),
            data={"time-taken": time_ns() - self.time_start},
            timestamps={"time-taken": 0.0},
        )
