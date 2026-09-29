from bluesky_nexus import NxDevice


@NxDevice.add_device_from_path("Keithley.yaml")
class Keithley(Device):
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
