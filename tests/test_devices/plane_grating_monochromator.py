from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    CalculatableTimeout,
    FlyMotorInfo,
    StandardReadable,
    WatchableAsyncStatus,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.core import (
    StandardReadableFormat as Fmt,
)
from ophyd_async.sim import SimMotor

from bluesky_nexus.nx_device._decorator import NexusDevices


@NexusDevices.add_device_from_path("PlaneGratingMonochromator.yaml")
class PlaneGratingMonochromator(StandardReadable):
    """A simulated plane grating monochromator."""

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)

        with self.add_children_as_readables():
            self.energy = SimMotor(name="energy", instant=False, units="eV")
            self.exit_slit = SimMotor(name="exit_slit", units="mm")
        with self.add_children_as_readables(format=Fmt.CONFIG_SIGNAL):
            self.diffraction_order = soft_signal_rw(int)
            self.grating_number = soft_signal_rw(str)
            self.grating, _ = soft_signal_r_and_setter(int)
            self.maxumum_energy, _ = soft_signal_r_and_setter(float)
            self.minimum_energy, _ = soft_signal_r_and_setter(float)
            self.cff = soft_signal_rw(float)  # SetCff

    # Make it so that this device performs on it's energy movable.
    def prepare(self, value: FlyMotorInfo) -> AsyncStatus:
        return self.energy.prepare(value)

    def kickoff(self) -> AsyncStatus:
        return self.energy.kickoff()

    def complete(self) -> WatchableAsyncStatus:
        return self.energy.complete()

    def set(self, new_position: float, timeout: CalculatableTimeout = DEFAULT_TIMEOUT):
        return self.energy.set(new_position=new_position, timeout=timeout)

    def stop(self, success: bool = False):
        return self.energy.stop(success=success)
