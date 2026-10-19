# Nexus Structure

At it's core, the `bluesky_nexus` package is for defining a standard correspondence between NeXus structures and bluesky runs.

Any bluesky run produces a nexus structure:

```
2026_08_17_15_32_10_count:NXroot
  @HDF5_Version = '2.0.0'
  @creator = 'nexusformat'
  @creator_version = '2.0.3'
  @file_name = '/tmp/pytest-of-a5497/pytest-117/test_structure...'
  @file_time = '2026-08-17T15:32:10.310540'
  @h5py_version = '3.16.0'
  entry:NXentry
    Application name = 'bluesky_nexus'
    Application version = '1.3.0.dev56+g90cc5e652.d20260817'
    Content = 'A bluesky run's documents parsed to nexus.'
    baseline:NXcollection
      <...>
    primary:NXcollection
      @description = ' A group of devices all read together.'
      devices:NXinstrument
        some_primary_pv_positioner:NXsubentry
          @nxclass = 'NXsubentry'
          acceleration:NXlog
            time = -0.0040607452392578125
              @units = 's'
            value = 1
          setpoint:NXlog
            time = [-0.004149 -0.004149]
              @units = 's'
            value = [0 0]
          some_primary_pv_positioner:NXlog
            time = [-0.004148 -0.004148]
              @units = 's'
            value = [0 0]
          velocity:NXlog
            time = -0.0040700435638427734
              @units = 's'
            value = 1
      stream_info:NXcollection
        descriptor:NXcollection
          <ENTIRE DESCRIPTOR OF STREAM INCLUDED>
        time:NXdata
          @axes = 'sequence_number'
          @signal = 'time'
          sequence_number = [1 2]
          time = [0.005075 0.005995]
            @units = 'S'
    run_info:NXcollection
      run_start:NXcollection
        <ENTIRE RUN START INCLUDED>
      run_stop:NXcollection
        <ENTURE RUN STOP INCLUDED>
```

* Relevant versions of the version are included in the `NXroot`.
* The run start and run stop documents are parsed into `run_info`.
* Streams are parsed into individual groups under `entry`.
* The information about the stream in parsed into `stream_info`. This is the event descriptor and the NXdata for the time each seq num was read.
* Devices read in a stream are stored in `devices`. For more on device structure see [](device_nexus_structure/nexus_structure.md)

The main philosophy of bluesky nexus is to define a structure for any bluesky run and allow further structure to be imposed on top.
