import time

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Kind


class Keithley(Device):
    readback = Cpt(EpicsSignalRO, "rdCur", kind=Kind.hinted, labels={"detectors", "electrometers"})
    init_cmd = Cpt(EpicsSignal, "cmdStart", kind=Kind.omitted)
    abort_cmd = Cpt(EpicsSignal, "cmdCancel", kind=Kind.omitted)
    trigger_cmd = Cpt(EpicsSignal, "rdCur.PROC", kind=Kind.omitted)

    zero_check = Cpt(EpicsSignal, "cmdZeroCheck", kind=Kind.config)
    zero_correct = Cpt(EpicsSignal, "cmdZeroCorrect", kind=Kind.config)
    measure_delay = Cpt(EpicsSignal, "rdCur.MDEL", kind=Kind.config)

    function = Cpt(EpicsSignal, "rbkFunc", write_pv="setFunc", string="True", kind=Kind.config)
    reset = Cpt(EpicsSignal, "cmdReset.PROC", kind=Kind.config)
    scan = Cpt(EpicsSignal, "fwdMeas.SCAN", string="True", kind=Kind.config)

    range_current = Cpt(
        EpicsSignal, "rbkRangeCur", write_pv="setRangeCur", string="True", kind=Kind.config
    )
    auto_range_current = Cpt(EpicsSignal, "rbkRangeCurAuto", string="True", kind=Kind.config)
    auto_range_current_lower_limit = Cpt(EpicsSignal, "setRangeCurAutoLLIM", kind=Kind.config)
    auto_range_current_upper_limit = Cpt(EpicsSignal, "setRangeCurAutoULIM", kind=Kind.config)

    number_power_line_cycles = Cpt(
        EpicsSignal, "rbkIntegrTime", write_pv="setIntegrTime", kind=Kind.config
    )
    integration_time = Cpt(
        EpicsSignal, "rbkIntegrTimeSec", write_pv="setIntegrTimeSec", kind=Kind.config
    )
    median_filter_rank = Cpt(
        EpicsSignal, "rbkFiltMedRnk", write_pv="setFiltMedRnk", kind=Kind.config
    )
    median_filter_enable = Cpt(
        EpicsSignal, "rbkFiltMedEnable", write_pv="cmdFiltMedEnable", kind=Kind.config
    )

    average_filter_count = Cpt(
        EpicsSignal, "rbkFiltAverCnt", write_pv="setFiltAverCnt", kind=Kind.config
    )
    average_filter_enable = Cpt(
        EpicsSignal, "rbkFiltAverEnable", write_pv="cmdFiltAverEnable", kind=Kind.config
    )

    arm_source = Cpt(
        EpicsSignal, "rbkArmSrc", write_pv="setArmSrc", string="True", kind=Kind.config
    )
    trigger_source = Cpt(
        EpicsSignal, "rbkTrgSrc", write_pv="setTrgSrc", string="True", kind=Kind.config
    )
    trigger_delay = Cpt(EpicsSignal, "rbkTrgDly", write_pv="setTrgDly", kind=Kind.config)

    model = Cpt(EpicsSignalRO, "idn", kind=Kind.config)

    front_panel_enable = Cpt(
        EpicsSignal, "rbkDisp", write_pv="cmdDisp", string="True", kind=Kind.config
    )  # default to "On"

    def __init__(self, prefix: str, *, name: str | None = None, **kwargs) -> None:
        super().__init__(prefix=prefix, name=name, **kwargs)
        self.readback.name = self.name

    def stage(self) -> list[object]:
        self.scan.set("1 Second").wait()
        self.init_cmd.set(1).wait()
        self.measure_delay.set(-1).wait()
        return super().stage()

    def unstage(self):
        time.sleep(1.0)
        self._set_and_wait(self.scan, ".1 second")
        return super().unstage()

    def trigger(self):
        return self.trigger_cmd.set(1)

keithley = Keithley("SOME-PREFIX", name="my-keithely")
assert keithley.hints == {'fields': ['my-keithely']}
