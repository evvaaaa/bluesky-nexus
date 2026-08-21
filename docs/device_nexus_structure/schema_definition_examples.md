# Examples

## Defining an ophyd Keithley as an [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html)

I would like to define some structure on my ophyd keithley device so that it can be understood to be an [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html). 

This device currently has no `NX_schema`

```{include} ../_static/examples/example_keithley_1_device.py
:code: python

```

To define some, I'm going to create a new file `Keithely.yaml` in the same directory as where my device definition of `Keithley` is. The definition will map data keys that will be read on the device to their fields in [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html).

```{include} ../_static/examples/Keithley.yaml
:code: yaml

```

1) `$nxclass` is a NeXus attribute which has to come from a constant. It's presence in a level of the schema indicates whether that level is a NeXus group. `bluesky_nexus` provides some light validation against this field using the [defined basemodels](#bluesky_nexus.nx_nexusformat_schema). If you supply an incorrect type, or a required item is missing in the supplied schema, then an error will be raised by the decorator.
2) The first four definitions simply map the data keys in the device (minus the name of the instance) to their name in the nexus schema. Since all data keys are added to the structure, it wouldn't be strictly necessary to map these if the data key name were already equal to the name in the nexus structure... This isn't always possible.
3) `data` is mapping to the `readback` data key. `readback` is given the same name as the device itself as a datakey, an so the name we use with it "" is.
4) {`timestamps_of_data_key`: ""} will give 
5) The last four are constant fields for all keithley. If any subclass of this Keithley wanted to override them, then they could in their own schema.

```{include} ../_static/examples/example_keithely_2_device.py
:code: python

```

Now when any instance of `Keithley` is read, `bluesky_nexus` will place the structure into an `NXdetector`. As you can see from the below image (silx viewer), all the data keys we didn't reference in our schema are also present in the NeXus structure.

## Simulated Monochromator

A monochromator is a substantially more complicated to define than the above. Shown below is an ophyd async sim device based off a [monochromator class we have defined at bessyii](https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bessyii-bluesky-devices/-/blob/d0ec7b2818eb48322b05d83d66236e4ddf40fc19/src/bessyii_bluesky_devices/devices/mono/energy.py#L21).

```{include} ../_static/examples/example_mono_1_devices.py
:code: python

```

[Set up a run engine](../using_the_nexus_structure.md) subscribed to our nexus writer callback:

```{include} ../_static/examples/example_re_file_writer.py
:code: python

```

... and run the plan:

```{include} ../_static/examples/example_mono_plan.py
:code: python

```

We can open the file in whatever nexus viewer. Here's `silx view *.nxs`:

```{image} silx_example_mono_1_1.png

```

All the data keys are present. Notice that

1) NeXus names have automatically converted `"-"` to  `"_"`. This is because `"-"` is not permitted in NeXus keys.
2) All numerical data is automatically an `NXlog` with it's timestamps. String data is not accepted in an `NXlog` so only the field is given.
3) Configuration data keys and read data keys live alongside each other. `bluesky_nexus` makes no distinction between the two.

It's time to describe this as a monochromator.

We make a new schema called `PlanGratingMonochromator.yaml` and include it in the directory where I'm defining my device.

```{include} ../_static/examples/PlaneGratingMonochromator.yaml
:code: yaml

```
1) The class attribute `$nxclass: NXmonochromator` is used. This group is a nexusformat [`NXmonochromator`](https://manual.nexusformat.org/classes/base_classes/NXmonochromator.html), and the schema will be validated against [`bluesky_nexus.nx_nexusformat_schema.NxMonochromator`](#bluesky_nexus.nx_nexusformat_schema.NxMonochromator).
2) The readback field `energy-readback` is given the name `energy` to conform to the NeXus base class.
3) A sub group is made for the exit slit. `NXmonochromator` expects exit slits to be defined in [a subgroup with this name](https://manual.nexusformat.org/classes/base_classes/NXmonochromator.html#nxmonochromator-exit-slit-group). The data keys relevant to exit slit are mapped here. The `$nclass: NXaperture` will mean that the sub group definitions will be making an [`NXaperture`](https://manual.nexusformat.org/classes/base_classes/NXaperture.html) and validated against [`bluesky_nexus.nx_nexusformat_schema.NxMonochromator`](#bluesky_nexus.nx_nexusformat_schema.NxAperture).
4) `diff_order` is not part of `NXmonochromator`, but we would like to give it a full name when it's written instead of the shortened data key.
5) We define some filters which are relevant to the monochromator. The coordinates of the transformations for both are used given as constants. Since "depends_on" is not supplied, the structure defaults to `"."` - the [standard NeXus coordinate system](https://manual.nexusformat.org/design.html#the-nexus-coordinate-system).
6) We give the full name of constant fixed focus, we also overwrite the units we get through EPICS to the standard that NeXus expects.
7) The class defines `GRATING` generic sub group(s). We include one with the units we can define.
8) Alpha beta and gamma make more sense in their own subgroup. We provide long names to better describe them.

Now we load the schema into our device. Any obvious errors we've made in our schema across the group and subgroups will be caught by pydantic.

```{note}
The pydantic schema cannot validate whether the data keys specified will actually end up being read by the device. It can only verify that, should they exist, the specification given will be a correct `NXmonochromator`.

This project would like to investigate being able to specify schema through annotations on declarative devices, which would make the validation that data keys exist tautological.
```

```{include} ../_static/examples/example_mono_2_devices.py
:code: python

```

... and run the plan again. Now viewing my file in sphinx, I can see that:


```{image} silx_example_mono_2_1.png
```

1) All units are correct. Units taken from the signal have been parsed. The units I specified in `constant_fixed_focus` have been used instead of those from the signal.
2) All groups and subgroups have the correct classes.
3) The long names I gave the transformations have been saved to their attributes. Their units have been parsed from the signal. 
