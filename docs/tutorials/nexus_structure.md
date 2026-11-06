# Device Schema Specification

```{seealso}
This is an explantion of the schema format. It may be confusing to some users who are less familiar with NeXus, or with ophyd/ophyd-async. For examples on how to define device schema which you can follow along with see [](./schema_definition_examples.md).
```

There are [6 types of nexus structure](https://manual.nexusformat.org/design.html#nexus-objects-and-terms) in total. `bluesky-nexus` is a package which maps bluesky specified data into NeXus data.

`bluesky_nexus` has a schema specification for mapping a bluesky `Readable` into a NeXus base class structure using [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass) and [`NxDevice`](#bluesky_nexus.device.NxDevice)

## 1. Making an [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass)

`bluesky_nexus` will by generate a default NeXus structure for any bluesky `Readable` over event documents. Structure can be imposed on top of this in a `Readable` by inheriting from [`NxDevice`](#bluesky_nexus.device.NxDevice) and supplying an [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass) schema.

This schema should be thought of as a mapping between NXDL classes and the data keys that will be produced by an instance of that device class when it's read. Each schema is an instance of a pydantic class defining the nexus base class of the device.

This schema is To generate the pydantic class from some NXDL, e.g [`NXobject`](https://github.com/nexpy/nexusformat/blob/main/src/nexusformat/definitions/base_classes/NXobject.nxdl.xml),use  [`NxBaseClass.build`](#bluesky_nexus.schema.NxBaseClass.build):

``` python
NxObject = NxBaseClass.build("NXobject")
```

This class will validate your `bluesky_nexus` specification in the device layer against the [`NXobject`](https://github.com/nexpy/nexusformat/blob/main/src/nexusformat/definitions/base_classes/NXobject.nxdl.xml) NXDL.

```{note}
You can toggle the local directory that your `NxBaseClass.build` loads NXDL from by setting the `BLUESKY_NEXUS_DEFINITIONS_DIRECTORY` environment variable. This variable should contain a directory called `base_classes` containing all the `.nxdl.xml` base class definitions which you could build `NxBaseClass` type with.
```


## 2. Providing Schema with [`NxDevice`](#bluesky_nexus.device.NxDevice)

The schema is supplied by inheriting from [`NxDevice`](#bluesky_nexus.device.NxDevice) and defining the class variable `BLUESKY_NEXUS_BASE_CLASS` with either an instance, or type of [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass).

We want the following ophyd device to have a structure corresponding to [`NXdetector`](https://github.com/nexpy/nexusformat/blob/main/src/nexusformat/definitions/base_classes/NXdetector.nxdl.xml):

``` python
class SomeDevice(Device):
    some_signal = Cpt(EpicsSignal, "SIGNAL")
```

All the below methods give the same schema when `.hints` is called on an instance of the device.

``` python
print(SomeDevice(name="meh").hints)
# {'NX_class': 'NXdetector', 'NX_schema': {'data': 'some_signal', '$nxclass': 'NXdetector'}}
```

### As an instance

An instance of the schema can be supplied to the class:

``` python
NxDetector = NxBaseClass.build("NXdetector")
class SomeDevice(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxDetector(
        data=NxField(data_key="some_signal")
    )
    some_signal = Cpt(EpicsSignal, "SIGNAL")
```

`bluesky_nexus` can now use the structure embedded in the hints of device instances to place it in the NeXus structure as an `NXdetector` 

### Serialized schema

Instances of [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass) have their own serialized syntax. For examples of this syntax, see [Defining your Schema](#defining-your-schema).

The below two examples are equivalent to the direct instantiation provided above.

#### Deserializing with [`NxBaseClass.from_dictionary`](#bluesky_nexus.schema.NxGroup.from_dictionary)

``` python
class SomeDevice(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_dictionary(
        {"$nxclass": "NXdetector", "data": "some_signal"}
    )
    some_signal = Cpt(EpicsSignal, "SIGNAL")
```


#### Deserializing with yaml - [`NxBaseClass.from_path`](#bluesky_nexus.schema.NxGroup.from_path)

``` python
# In some_module/some_device.py
class SomeDevice(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_path("some_device.yaml")
    some_signal = Cpt(EpicsSignal, "SIGNAL")
```


``` yaml
# In some_module/some_device.yaml
$nxclass: "NXdetector"
data: some_signal
```


where the yaml is relative to where the wrapper is being called

```
├── some_device.py
└── some_device.yaml
```

### As a Type (declarative definitions)

If a type of [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass) is provided instead of an instance, then `bluesky_nexus` will create the schema using [`annotations`](#bluesky_nexus.device.annotations).

This is only recommended to be used on [ophyd-async declarative devices](https://blueskyproject.io/ophyd-async/main/explanations/declarative-vs-procedural.html).


``` python
NxDetector = NxBaseClass.build("NXdetector")
class SomeDevice(NxDevice, StandardReadable, EpicsDevice):
    BLUESKY_NEXUS_BASE_CLASS = NxDetector
    some_signal: Annotated[SignalRW[float], PvSuffix("SIGNAL"), NxDataKey("data")]
```

(defining-your-schema)=
## Defining your Schema

### Fields

The nexus [field](https://manual.nexusformat.org/design.html#design-fields) type is defined with the `bluesky_nexus` [`NxField`](#bluesky_nexus.schema.NxField). This model links a nexus field in the outputted structure with:

* A `data_key`, minus the name of the object at instantiation, and the initial separator.
* A `constant` defined in the schema. This should be used in the case of fields in the nexus format which would almost never be received through a signal, e.g location of a detector.
* A `hints_key` - another field in hints e.g ['metadata', "description"]. At bessyii, we can provide metadata to the instance through [our static yaml definitions during instantiation](https://codebase.helmholtz.cloud/hzb/bluesky/core/source/device-instantiation-map).

In consumers, for any field defined in schema, if the field isn't present when the data is received there is no fail state. They simply aren't written into the structure.

``` python
class SomeDevice(NxDevice, Device):
    NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXobject", "a_different_name": "some_signal",
            "description": {"constant": "A description..."}
        }
    )
    some_signal = Cpt(EpicsSignalRO, "SUFFIX")

```

```{note}
As you may have gathered from the above `a_different_name: some_signal` is shorthand. Since the vast
majority of schema will not define any attributes on the field, and will come directly from a data key. Therefore
we allow the shorthand `a_different_name: some_signal` instead of `a_different_name: {data_key: some_signal}`
```

### Attributes

[Attributes](https://manual.nexusformat.org/design.html#design-attributes) define metadata on groups/fields. This isn't scan data which to be plotted, but relevant metadata on the field/signal which should be stored in the structure.

It has the same methods for definition as the above, with the only differences being:
* An attribute cannot itself contain an attribute.
* In the serialized schema, attributes are defined with the `$` prefix on keys.
* In the serialized schema the shorthand for attributes is constant.

The [`NxAttribute`](#bluesky_nexus.schema.NxAttribute) model links to nexus attributes in the structure.

Every nexus group has the attribute `nxclass` which defines which NeXus base class it corresponds to.

#### Example

``` python
class SomeDevice(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxObject(
        a_different_name=NxField(
            data_key="some_signal",
            units=NxAttribute(constant="yard/s")
        ),
        description=NxField(
            constant="A description...",
            long_name=NxAttribute(constant="A longer description")
        ),
        long_name=NxAttribute(constant="My very special device")
    )
    some_signal = Cpt(EpicsSignalRO, "PREFIX")
```

``` yaml
$nxclass: NXobject
a_different_name: {data_key: some_signal, $units: "yard/s"}
description: {constant: "A description...", $long_name: "My very special device"}
$long_name: "My very special device"
```

``` {note}
The units attribute is accepted on every nexus field. If not specified in the schema with `$units`, this is automatically given to the field from the units received through bluesky.
```

### Sub Groups

Sub groups can be specified through the tree structure

``` python
class SomeDevice(NxDevice, Device):
    BLUESKY_NEXUS_BASE_CLASS = NxObject(
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

    some_signal = Cpt(EpicsSignalRO, "PREFIX1")
    some_sub_device_signal = Cpt(SomeSubDevice, "PREFIX2")
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

  * If in the pydantic schema there is a field or attribute required and it was not provided in the serialized yaml, there will be an error on [`NxBaseClass`](#bluesky_nexus.schema.NxBaseClass) instantiation.
  * If there is a subgroup or field which is optional, but you decide to provide it, it will be validated against the structure.
```

### Declarative Behaviour

With a declarative device, e.g one where `BLUESKY_NEXUS_BASE_CLASS` is a type of NXDL, the schema is built from the annotations when `hints` is called. In bluesky this happens when the stream is opened.

When this happens, the device is parsed for annotations.

There are three types of bluesky nexus annotations:

* [`NxDataKey`](#bluesky_nexus.device.NxDataKey) - For attributes which are data keys.
* [`NxConstant`](#bluesky_nexus.device.NxConstant) - For json serializable variables on the class.
* [`NxSubGroup`](#bluesky_nexus.device.NxSubGroup) - For sub devices which should be mapped to a subgroup in the NeXus structure.

Each of [`NxDataKey`](#bluesky_nexus.device.NxDataKey) and [`NxConstant`](#bluesky_nexus.device.NxConstant) can take the argument `is_nx_attribute` (default `False`) to have the data key or constant map to an NeXus attribute instead of a field.

As an example, this device implements all the kinds of annotations.

``` python
NxDetector = NxBaseClass.build("NXdetector")
NxObject = NxBaseClass.build("NXobject")

class SomeSubDevice(NxDevice, StandardReadable, EpicsDevice):
    BLUESKY_NEXUS_BASE_CLASS = NxObject
    signal1: Annotated[SignalRW[float], PvSuffix("SIGNAL1"), NxDataKey("field1")]
    signal2: Annotated[
        SignalRW[float], PvSuffix("SIGNAL2"), NxDataKey("attribute1", is_nx_attribute=True)
    ]
    SOME_CONSTANT_1: Annotated[int, NxConstant("field2")] = 1
    SOME_CONSTANT_2: Annotated[int, NxConstant("attribute2", is_nx_attribute=True)] = 2

class SomeDevice(NxDevice, StandardReadable, EpicsDevice):
    BLUESKY_NEXUS_BASE_CLASS = NxObject
    signal1: Annotated[SignalRW[float], PvSuffix("SIGNAL1"), NxDataKey("field1")]
    signal2: Annotated[
        SignalRW[float], PvSuffix("SIGNAL2"), NxDataKey("attribute1", is_nx_attribute=True)
    ]
    SOME_CONSTANT: Annotated[int, NxConstant("field2")] = 1
    SOME_CONSTANT: Annotated[int, NxConstant("attribute2", is_nx_attribute=True)] = 2

    some_sub_device: Annotated[SomeSubDevice, NxSubGroup("sub_group"), PvSuffix("SUB")]

print(SomeDevice(name="foo").hints)
# {
#   'NX_class': 'NXobject',
#   'NX_schema': {
#       'sub_group': {
#           'field1': 'some_sub_device-signal1',
#           'field2': {'constant': 1},
#           '$attribute1': {'data_key': 'some_sub_device-signal2'},
#           '$attribute2': 2,
#           '$nxclass': 'NXobject'
#       },
#       'field1': 'signal1',
#       '$attribute1': {'data_key': 'signal2'},
#       '$attribute2': 2,
#       '$nxclass': 'NXobject'
#   }
# }
```
