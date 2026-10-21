from bluesky_nexus.device import NxDevice
from bluesky_nexus.schema.nx_base_class import NxBaseClass


class PlaneGratingMonochromator(NxDevice, StandardReadable):
    """A simulated plane grating monochromator."""

    BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_path("PlaneGratingMonochromator.yaml")

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
            self.alpha, _ = soft_signal_r_and_setter(float, initial_value=1.47, units="deg")
            self.beta, _ = soft_signal_r_and_setter(float, 3.23, units="deg")
            self.theta, _ = soft_signal_r_and_setter(float, initial_value=2.4, units="deg")
