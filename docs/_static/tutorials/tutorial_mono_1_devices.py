from ophyd.signal import DEFAULT_TIMEOUT
from ophyd_async.core import (
    DeviceMock,
    StandardReadable,
    StrictEnum,
    callback_on_mock_put,
    set_mock_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
    DEFAULT_TIMEOUT,
)
from ophyd_async.core import (
    StandardReadableFormat as Fmt,
    AsyncStatus
)
import asyncio


class ExitSlitBranch(StrictEnum):
    SISSY1 = "SISSY1"
    OAESE = "OAESE"
    CAT = "CAT"


class ExitSlit(StandardReadable):
    def __init__(self, initial_value: float = 0.0, name: str = "") -> None:
        super().__init__(name=name)
        with self.add_children_as_readables():
            self.value = soft_signal_rw(float, initial_value=initial_value, units="um")
        with self.add_children_as_readables(Fmt.CONFIG_SIGNAL):
            self.selected_branch = soft_signal_rw(ExitSlitBranch)


class GratingTranslationSelectionOptions(StrictEnum):
    POSITION_UNDEFINED = ""
    POSITION_400 = "400l/mm"
    POSITION_800 = "800l/mm"


class GratingTranslation(StandardReadable):
    def __init__(self, name: str = ""):
        super().__init__(name=name)

        with self.add_children_as_readables():
            self.translation= soft_signal_rw(
                float, initial_value=800., units="l/mm"
            )
        with self.add_children_as_readables(Fmt.CONFIG_SIGNAL):
            self.selection = soft_signal_rw(
                GratingTranslationSelectionOptions, initial_value=GratingTranslationSelectionOptions.POSITION_800
            )

    async def connect(self, mock: bool | DeviceMock = False, timeout: float = DEFAULT_TIMEOUT, force_reconnect: bool = False) -> None:
        await super().connect(mock, timeout, force_reconnect)
        callback_on_mock_put(
            self.selection, self._add_position_from_selector
        )
        callback_on_mock_put(
            self.translation, self._set_position_selector_to_undefined
        )

    async def _set_position_selector_to_undefined(self, value: float):
        if value not in (800., 400.):
            set_mock_value(self.selection, GratingTranslationSelectionOptions.POSITION_UNDEFINED)

    async def _add_position_from_selector(self, value: GratingTranslationSelectionOptions):
        if value is GratingTranslationSelectionOptions.POSITION_400 or value is GratingTranslationSelectionOptions.POSITION_800:
            await self.translation.set(float(value.value.removesuffix("l/mm")))

class Filter(StandardReadable):
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)

        with self.add_children_as_readables():
            self.value = soft_signal_rw(float, units="deg", initial_value=0.8)

        with self.add_children_as_readables(Fmt.CONFIG_SIGNAL):
            self.enabled = soft_signal_rw(bool, initial_value=True)


class Harmonic(StrictEnum):
    FIRST = "1st Harmonic"
    THIRD = "3rd Harmonic"
    FIFTH = "5th Harmonic"
    SEVENTH = "7th Harmonic"
    NINTH = "9th Harmonic"
    ELEVENTH = "11th Harmonic"
    THIRTEENTH = "13th Harmonic"
    MAX_FLUX = "Max Flux"
    AUTO = "Auto"


class Energy(StandardReadable):
    def __init__(self, name: str = "", initial_value: float = 0.0):
        super().__init__(name=name)
        with self.add_children_as_readables():
            self.setpoint = soft_signal_rw(float, units="eV", initial_value=initial_value)
            self.readback = soft_signal_rw(float, units="eV", initial_value=initial_value)
        with self.add_children_as_readables(Fmt.CHILD):
            self.velocity = soft_signal_rw(float, units="eV/s", initial_value=1)
        self.sweep_offset = soft_signal_rw(float, initial_value=0.0)


    @AsyncStatus.wrap
    async def set(self, value: float):
        await self.setpoint.set(value)
        await self.readback.set(value)


class PlaneGratingMonochromator(StandardReadable):
    """A simulated plane grating monochromator."""

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)

        with self.add_children_as_readables():
            self.energy = Energy(initial_value=545.0)
            self.exit_slit = ExitSlit(initial_value=30)
            self.mirror2_translation = soft_signal_rw(float, initial_value=291.02, units="mm")
            self.phi = Filter()
            self.psi = Filter()
            self.grating = GratingTranslation()

        with self.add_children_as_readables(format=Fmt.CONFIG_SIGNAL):
            self.harmonic = soft_signal_rw(Harmonic, initial_value=Harmonic.THIRD)

            self.maxumum_energy, _ = soft_signal_r_and_setter(
                float, initial_value=1253.5, units="eV"
            )
            self.minimum_energy, _ = soft_signal_r_and_setter(
                float, initial_value=251.2, units="eV"
            )

            self.diff_order, _ = soft_signal_r_and_setter(int, initial_value=1)
            self.grating_number, _ = soft_signal_r_and_setter(int, initial_value=0)
            self.cff = soft_signal_rw(float, initial_value=2.25)
            self.alpha = soft_signal_r_and_setter(float, initial_value=1.47, units="deg")
            self.beta = soft_signal_r_and_setter(float, 3.23, units="deg")
            self.theta = soft_signal_r_and_setter(float, initial_value=2.4, units="deg")
