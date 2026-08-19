from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
    callback_on_mock_put,
    set_mock_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.core import (
    StandardReadableFormat as Fmt,
)
from ophyd_async.sim import SimMotor


class ExitSlitBranch(StrictEnum):
    SISSY1 = "SISSY1"
    OAESE = "OAESE"
    CAT = "CAT"


class ExitSlit(SimMotor):
    def __init__(self, initial_value: float = 0.0, name: str = "") -> None:
        super().__init__(name, initial_value=initial_value, units="um")
        with self.add_children_as_readables(Fmt.CONFIG_SIGNAL):
            self.exit_slit_branch = soft_signal_rw(ExitSlitBranch)


class GratingTranslation(StrictEnum):
    POSITION_UNDEFINED = ""
    POSITION_400 = "400l/mm"
    POSITION_800 = "800l/mm"


class Grating(StandardReadable):
    def __init__(self, name: str = ""):
        super().__init__(name=name)
        with self.add_children_as_readables():
            self.grating_translation = soft_signal_rw(float, initial_value=799.99, units="l/mm")
            self.grating_translation_selection = soft_signal_rw(
                GratingTranslation, initial_value=GratingTranslation.POSITION_800
            )
            callback_on_mock_put(
                self.grating_translation_selection, self._add_position_from_selector
            )
            callback_on_mock_put(
                self.grating_translation, self._set_position_selector_to_undefined
            )

    async def _set_position_selector_to_undefined(self, value: float):
        set_mock_value(self.grating_translation_selection, GratingTranslation.POSITION_UNDEFINED)

    async def _add_position_from_selector(self, value: GratingTranslation):
        if value is GratingTranslation.POSITION_400 or value is GratingTranslation.POSITION_800:
            set_mock_value(self.grating_translation, float(value.value.removesuffix("l/mm")))


class Filter(StandardReadable):
    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        with self.add_children_as_readables():
            self.angle = soft_signal_rw(float, units="deg", initial_value=0.8)
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


class Energy(SimMotor):
    def __init__(self, name: str = "", initial_value: float = 0.0):
        super().__init__(name=name, initial_value=initial_value, units="eV")


class PlaneGratingMonochromator(StandardReadable):
    """A simulated plane grating monochromator."""

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)

        with self.add_children_as_readables():
            self.energy = Energy(name="energy", initial_value=545.0)
            # TODO: verify all these PVs
            self.exit_slit = ExitSlit(name="exit_slit", initial_value=30)
            self.mirror2_translation = SimMotor(initial_value=291.02, units="mm")
            self.phi = Filter()
            self.psi = Filter()

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
            self.grating, _ = soft_signal_r_and_setter(float, initial_value=800.0, units="l/mm")
            self.cff = soft_signal_rw(float, initial_value=2.25)
            self.alpha = soft_signal_r_and_setter(float, initial_value=1.47, units="deg")
            self.beta = soft_signal_r_and_setter(float, 3.23, units="deg")
            self.theta = soft_signal_r_and_setter(float, initial_value=2.4, units="deg")
            self.sweep_offset = soft_signal_rw(float, initial_value=0.0)
