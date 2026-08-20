# Nexus Structure

At it's core, the `bluesky_nexus` package is for defining a standard correspondence between NeXus structures and bluesky runs.

## Generated structure

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
* Devices read in a stream are stored in `devices`.
* Data keys are stripped of the objects name, and the initial first separator. In the case where the datakey name is equal to the object name, the name is preserved.

The main philosophy of bluesky nexus is to define a structure for any bluesky run and allow further structure to be imposed on top.

## Device Schema Specification

```{seealso}
This is an explantion of the schema format. For examples on how to define schema which you can follow along with see [](./schema_definition_examples.md).
```

There are [6 types of nexus structure](https://manual.nexusformat.org/design.html#nexus-objects-and-terms) in total. `bluesky_nexus` allows for defining groups, fields, and attributes on a bluesky device class though a schema specification. This schema should be thought of as a mapping between NXDL classes, and the data keys that will be produced by an instance of that device class when it's read. Each schema is an instance of a pydantic class defining the nexus base class of the device [`nx_nexusformat_schema`](#bluesky_nexus.nx_nexusformat_schema).

Bluesky nexus provides the [`NexusDevices`](#bluesky_nexus.nx_device._decorator.NexusDevices) decorator to add schema. It can load from one of three sources:

1) From pydantic schema directly.
2) A dictionary directly.
3) A yaml path, either relative to the device class file, or absolute.

```{note}
A main goal of bluesky nexus will be to support custom schema for whichever NXDL. Currently only those in nexusformat are provided, though it is hoped that future developments will make it possible to load a custom package representing whichever NXDL your facility uses.
```


### Groups

[Groups](https://manual.nexusformat.org/design.html#design-groups) are defined by subclasses of [`NxGroup`](#bluesky_nexus.nx_schema.NxGroup).

By default, `bluesky_nexus` gives all devices and their data keys the nexus structure `NXsubentry`, corresponding to the pydantic schema [`NxSubEntry`](#bluesky_nexus.nx_nexusformat_schema.NxSubEntry). There are a few different ways to define other kinds of group for a given device class instead:


#### From pydantic schema

In the pydantic schema this is defined by the type of the model itself.

``` python
@NexusDevices.from_schema(NxObject())
class SomeDevice(Device): ...
```

In the serialized schema, this is provided by an attribute called `nxclass`. When `NexusDevices` adds the schema it deserializes and instantiates, so the below two methods are equivalent to this one.

#### From dictionary


``` python
@NexusDevices.from_dictionary({"$nxclass": "NXobject"})
class SomeDevice(Device): ...
```

#### From yaml

``` python
@NexusDevices.from_dictionary("some_device.yaml")
class SomeDevice(Device): ...
```

where the yaml is relative to where the wrapper is being called

```
├── some_device.py
└── some_device.yaml
```

``` yaml
$nxclass: NXobject
```


### Fields



The nexus [field](https://manual.nexusformat.org/design.html#design-fields) type is defined with the `bluesky_nexus` [`NxField`](#bluesky_nexus.nx_schema.NxField). This model links a nexus field in the outputted structure with:

* A `data_key`, minus the name of the object at instantiation, and the initial separator.
* A `constant` defined in the schema. This should be used in the case of fields in the nexus format which would almost never be received through a signal, e.g location of a detector.
* A `hints_key` - another field in hints e.g ['metadata', "description"]. At bessyii, we can provide metadata to the instance through [our static yaml definitions during instantiation](https://codebase.helmholtz.cloud/hzb/bluesky/core/source/device-instantiation-map). The metadata on the instance is also added to the hints of a device. It has been decided that allowing additions from hints directly is a good general purpose solution for keys which may appear through multiple devices in the inheritance hierarchy.

For any field defined in schema, if the field isn't present when the data is received there is no fail state. They simply aren't written into the structure.

#### From pydantic schema

``` python
@NexusDevices.from_schema(
  NxObject(
    a_different_name=NxField(data_key="some_signal"),
    description=NxField(constant="A description...")
  )
)
class SomeDevice(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX")
```

#### From dictionary

``` python
@NexusDevices.from_dictionary(
  {
    "$nxclass": "NXobject", "a_different_name": "some_signal",
    "description": {"constant": "A description..."}
  }
)
class SomeDevice(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX")

```

#### From yaml

``` python
@NexusDevices.from_dictionary("some_device.yaml")
class SomeDevice(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX")
```


``` yaml
$nxclass: NXobject
a_different_name: some_signal
description: {constant: "A description..."}
```


```{note}
As you may have gathered from the above `a_different_name: some_signal` is shorthand. Since the vast
majority of schema will not define any attributes on the field, and will come directly from a data key. Therefore
we allow the shorthand `a_different_name: some_signal` instead of `a_different_name: {data_key: some_signal}`
```

### Attributes

[Attributes](https://manual.nexusformat.org/design.html#design-attributes) define metadata on groups/fields. This isn't data which is itself to be plotted, but relevant metadata on the field/signal which should be stored in the stucture.

It has the same methods for definition as the above, with the only differences being:
* An attribute cannot itself contain an attribute.
* In the serialized schema, attributes are defined with the `$` prefix on keys.
* In the serialized schema the shorthand for attributes is constant.

The [NxAttribute](#bluesky_nexus.nx_schema.NxAttribute) model links to nexus attributes in the structure.

#### Example

``` python
@NexusDevices.from_schema(
  NxObject(
    a_different_name=NxField(
      data_key="some_signal",
      units=NxAttribute(constant="yard/s")
    ),
    description=NxField(constant="A description...", long_name=NxAttribute),
    long_name=NxAttribute(constant="My very special device")
  )
)
class SomeDevice(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX")
```

``` yaml
$nxclass: NXobject
a_different_name: {data_key: some_signal, $units: "yard/s"}
description: {constant: "A description..."}
$long_name: "My very special device"
```

``` {note}
The units attribute is accepted on every nexus field. If not specified in the schema with `$units`, this is automatically given from the units received through bluesky.
```

### Sub Groups

Sub groups can be specified through the tree structure

``` python
@NexusDevices.from_schema(
  NxObject(
    a_different_name=NxField(
      data_key="some_signal",
      units=NxAttribute(constant="yard/s")
    ),
    description=NxField(constant="A description...", long_name=NxAttribute),
    long_name=NxAttribute(constant="My very special device"),
    sub_device_name_in_nexus_structure=NxObject(
      sub_device_signal_name_in_structure=NxField(data_key="some_sub_device_signal")
    )
  )
)
class SomeDevice(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX1")
  some_sub_device = Cpt(SomeSubDevice, "PREFIX2")
```

``` yaml
$nxclass: NXobject
a_different_name: {data_key: some_signal, $units: "yard/s"}
description: {constant: "A description..."}
$long_name: "My very special device"
sub_device_name_in_nexus_structure:
  $nxclass: NXobject
  sub_device_signal_name_in_structure: some_sub_device_signal
```

```{note}
  Groups are always validated against their pydantic schema.

  * If in the pydantic schema there is a field or attribute required and it was not provided in the serialized yaml, the decorator will raise an error.
  * If there is a subgroup or field which is optional, but you decide to provide it, it will be validated against the structure.
```

## Defining an [NXdata](https://manual.nexusformat.org/classes/base_classes/NXdata.html)

We shall take [`NxData`](#bluesky_nexus.nx_nexusformat_schema.NxData) as an example. I would like to define some structure on my ophyd keithley device so that it can be plotted.

... TODO

``` python
class Keithley(Device):
    init_cmd = Cpt(EpicsSignal, "cmdStart", kind=Kind.omitted)
    abort_cmd = Cpt(EpicsSignal, "cmdCancel", kind=Kind.omitted)
    trigger_cmd = Cpt(EpicsSignal, "rdCur.PROC", kind=Kind.omitted)

    readback = Cpt(EpicsSignalRO, "rdCur", kind=Kind.hinted, labels={"detectors", "electrometers"})
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

    front_panel_enable = Cpt(
        EpicsSignal, "rbkDisp", write_pv="cmdDisp", string="True", kind=Kind.config
    )  # default to "On"

    def __init__(self, prefix: str, *, name: str | None = None, **kwargs: Any) -> None:
        super().__init__(prefix=prefix, name=name, **kwargs)
        self.readback.name = self.name

    def stage(self) -> list[object]:
        self.scan.set("1 Second", wait=True)
        self.init_cmd.set(1, wait=True)
        self.measure_delay.set(-1, wait=True)
        return super().stage()

    def unstage(self) -> list[object]:
        time.sleep(1.0)
        self._set_and_wait(self.scan, ".1 second")
        return cast(list[object], super().unstage())

    def trigger(self, *) -> DeviceStatus:
        return self.trigger_cmd.set(1, wait=False)
```


Here is an annotated `NxData` we can understand.



## Inheritance

Unless `inherit=False` is given with

``` python
NexusDevice.from_schema(..., inherit=False)
```

then a given device will load the parent schema from it's parent devices, so long as those devices are NeXus subclasses of the one being loaded into the child device.

``` python
# https://manual.nexusformat.org/classes/base_classes/NXcomponent.html
# NXcomponent contains a field called description. We set any device to by default
# use the hints field "description" if it's present.
@NexusDevices.from_schema({"$nxclass": "NXcomponent", "description": {"hints_key": ["metadata", "description"]}})(Device)

# https://manual.nexusformat.org/classes/base_classes/NXaperture.html
# NXaperture extends NXcomponent, so this field will inherit the schema key from it's parent device.
@NexusDevices.from_schema({"$nxclass": "NXaperture", ...})
class MyAperture1(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX1")

# As a subclass, this "description" will overwrite the parent's description on this class
@NexusDevices.from_schema({"$nxclass": "NXaperture", "description": {"constant": "Some description."}, ...})
class MyAperture2(Device):
  some_signal = Cpt(EpicsSignalRO, "PREFIX1")
```

### Multi-Inheritance

Devices also support multi-inheritance of subgroups, attributes, and fields. The keys in the schema are overwritten from parent to child with the same priority as ordinary inheritance through python.

``` python
@NexusDevices.from_schema({"$nxclass": "NXaperture", "some_key": "parent_signal_1"})
class Parent1(Device):
  parent_signal_1 = Cpt(EpicsSignalRO, "PREFIX1")

@NexusDevices.from_schema({"$nxclass": "NXcomponent", "some_key": "parent_signal_21", "another_key": "parent_signal_22"})
class Parent2(Device):
  parent_signal_2 = Cpt(EpicsSignalRO, "PREFIX2")

# This schema has "some_key": parent_signal_1", and "another_key": "parent_signal_22".
# Left hand side is treated with priority just like python inheritance.
@NexusDevices.from_schema({"$nxclass": "NXaperture"})
class Child(Parent1, Parent2):
  child_signal = Cpt(EpicsSignalRO, "PREFIX3")
```


## Using The Nexus Structure

`bluesky_nexus.create_nexus_structure` defines a standard for how a bluesky run corresponds to a NeXus file. In this package we've provided two callbacks for using it.

### 1) With [`BlueskyNexusCallback`](#bluesky_nexus.BlueskyNexusCallback)

[`BlueskyNexusCallback`](#bluesky_nexus.BlueskyNexusCallback) is an abstract base class for setting up your own bluesky callbacks for using this structure. It processes the run into a nexus structure and then calls it's own abstract method 

``` python
process_nexus_structure(self, generated_structure: nexusformat.nexus.NXroot)
```

This class should be subclassed by other callbacks defining their own [`process_nexus_structure`](#bluesky_nexus.BlueskyNexusCallback.process_nexus_structure) to deal with the `NXroot` generated by a run.

### 2) With [`bluesky_nexus.NexusHdfWriterCallback`](#bluesky_nexus.NexusHdfWriterCallback)

[`bluesky_nexus.NexusHdfWriterCallback`](#bluesky_nexus.NexusHdfWriterCallback) is one callback subclassing [`BlueskyNexusCallback`](#bluesky_nexus.BlueskyNexusCallback) which dumps the generated nexus structure into hdf5 files. On initialization it takes the argument `output_root_directory: Path = Path(".")` as the directory to dump to. One file is generated per run.

This package contains a convenient `__main__` which can be used to start this callback over zmq or kafka.

To start with kafka, ensure `bluesky_nexus[kafka]` has been installed and run 

``` bash
$ python -m bluesky_nexus kafka
```

with the following positional arguments:

  - `root_output_directory` - Root directory for NeXus files.
  - `kafka_brokers` - Kafka bootstrap servers (e.g. 'host1:9092,host2:9092').
  - `kafka_group` - Kafka consumer group ID (e.g. nexus-writer).
  - `kafka_topic` - Kafka topic to subscribe to (e.g. bluesky.documents)

To start with zmq, ensure `bluesky_nexus[zmq]` has been installed and run 

``` bash
$ python -m bluesky_nexus zmq
```

with the following positional arguments:

  - `root_output_directory` - Root directory for NeXus files.
  - `zmq_ip` - ZeroMQ publisher IP.
  - `zmq_port` - ZeroMQ publisher port.


