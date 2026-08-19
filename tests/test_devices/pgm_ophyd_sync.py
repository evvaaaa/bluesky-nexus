# type: ignore
# ruff: noqa
"""Example that won't be initialized here."""


class Energy(PVPositioner):
    setpoint = Cpt(EpicsSignal, "monoSetEnergy", kind=Kind.normal)
    readback = Cpt(EpicsSignalRO, "monoGetEnergy", kind=Kind.hinted, labels={"motors", "monos"})
    done = Cpt(EpicsSignal, kind=Kind.omitted)
    done_status = Cpt(EpicsSignalRO, "IStatus", auto_monitor=True, kind=Kind.omitted)
    error_counter = Cpt(EpicsSignalRO, "ErrorCount", auto_monitor=True, kind=Kind.omitted)
    stop_signal = Cpt(EpicsSignal, "MonoAktion.PROC", kind=Kind.omitted)
    stop_value = 0
    readback_precision = 2


class ExitSlit(BaseComparitor):
    """Comparator-based exit-slit positioner."""

    setpoint = Cpt(EpicsSignal, "_Input")
    readback = Cpt(EpicsSignalRO, "_SW", kind=Kind.hinted, labels={"motors", "slits"})
    bandwidth = Cpt(
        EpicsSignalRO,
        "_BW",
    )  # in meV
    resolving_power = Cpt(EpicsSignalRO, "_ResPow")


class PGM(BaseEnergy):
    """Plane-grating monochromator device."""

    positioning_mode = Cpt(
        EpicsSignal,
        "multiaxis:mbbiMoveMode",
        write_pv="multiaxis:mbboSetMoveMode",
        string="True",
        kind=Kind.config,
    )

    # Energy selection.
    energy = Cpt(Energy, "")

    energy_minimum = Cpt(
        EpicsSignalRO,
        "minEnergy",
        kind=Kind.config,
    )

    energy_maxiumum = Cpt(
        EpicsSignalRO,
        "maxEnergy",
        kind=Kind.config,
    )

    cff = Cpt(EpicsSignal, "cff", write_pv="SetCff", kind=Kind.config)

    diffraction_order = Cpt(EpicsSignal, "Order", write_pv="SetOrder", kind=Kind.config)
    grating_number = Cpt(EpicsSignal, "SetGratingNo", string="True", kind=Kind.config)
    grating = Cpt(
        EpicsSignalRO,
        "lineDensity",
        kind=Kind.config,
    )

    exit_slit = Cpt(ExitSlit, "", ch_name="0")
    mirror2_translation = Cpt(MonoTranslationAxis, "", ch_num="0", labels={"pgm"})
    grating_translation = Cpt(MonoTranslationAxis, "", ch_num="1", labels={"pgm"})
    grating_translation_selection = Cpt(MonoTranslationAxisSelect, "", ch_num="1", labels={"pgm"})
    exit_slit = Cpt(EmilPgmExitSlit, "")

    alpha = Cpt(MonoAlphaBetaAxis, "", ch_name="Alpha", settle_time=10.0)
    beta = Cpt(MonoAlphaBetaAxis, "", ch_name="Beta", settle_time=10.0)
    theta = Cpt(MonoAlphaBetaAxis, "", ch_name="Theta", settle_time=10.0)
