# Device Nexus Structure

## Device Schema Specification

```{seealso}
This is an explantion of the schema format. It may be confusing to some users who are less familiar with NeXus, or with ophyd/ophyd-async. For examples on how to define device schema which you can follow along with see [](./schema_definition_examples.md).
```

There are [6 types of nexus structure](https://manual.nexusformat.org/design.html#nexus-objects-and-terms) in total. `bluesky_nexus` allows for defining base classes, fields, and attributes on a bluesky device class though a schema specification. Eventually, attributes will be added. This schema should be thought of as a mapping between NXDL classes, and the data keys that will be produced by an instance of that device class when it's read. Each schema is an instance of a pydantic class defining the nexus base class of the device.

This schema is loaded from NXDL with a metaclass: [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass).


Bluesky nexus provides the [`NexusDevices`](#bluesky_nexus.nexus_devices._decorator.NexusDevices) decorator to add schema. It can load from one of three sources:

1) From pydantic schema directly.
2) A dictionary directly.
3) A yaml path, either relative to the device class file, or absolute.

```{note}
A main goal of bluesky nexus will be to support custom schema for whichever NXDL. Currently only those in nexusformat are provided, though it is hoped that future developments will make it possible to load a custom package representing whichever NXDL your facility uses.
```


### Groups

[Groups](https://manual.nexusformat.org/design.html#design-groups) are defined by subclasses of [`NxGroup`](#bluesky_nexus.schema.NxGroup).

By default, `bluesky_nexus` gives all devices and their data keys the nexus structure `NXsubentry`, corresponding to the pydantic schema`NxBaseClass["NXsubentry"]`. There are a few different ways to define other kinds of group for a given device class instead:


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

The nexus [field](https://manual.nexusformat.org/design.html#design-fields) type is defined with the `bluesky_nexus` [`NxField`](#bluesky_nexus.schema.NxField). This model links a nexus field in the outputted structure with:

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

The [NxAttribute](#bluesky_nexus.schema.NxAttribute) model links to nexus attributes in the structure.

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

## Inheritance

### Single Inheritance

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


```{note}
A device does not have to use the decorator in order to inherit the schema from it's parent(s).
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
