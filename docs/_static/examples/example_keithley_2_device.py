from bluesky_nexus import NxDevice
from bluesky_nexus.schema.nx_base_class import NxBaseClass


class Keithley(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_path("Keithley.yaml")

    readback = Cpt(EpicsSignalRO, "rdCur", kind=Kind.hinted, labels={"detectors", "electrometers"})
    ... # And so on

keithley = Keithley("SOME-PREFIX", name="my-keithely")
assert keithley.hints == {'NX_class': 'NXdetector',
 'NX_schema': {'$nxclass': 'NXdetector',
               'acquisition_mode': {'constant': 'triggered'},
               'data': '',
               'description': {'constant': 'Keithley electrometer'},
               'layout': {'constant': 'point'},
               'raw_time_of_flight': 'number_power_line_cycles',
               'serial_number': 'model',
               'stop_time': {'timestamps_of_data_key': ''},
               'time_of_flight': 'integration_time',
               'trigger_delay_time_set': 'trigger_delay',
               'type': {'constant': 'Electrometer'}},
 'fields': ['my-keithely_readback']}
