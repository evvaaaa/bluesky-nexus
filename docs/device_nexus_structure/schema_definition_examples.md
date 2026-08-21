# Examples

## Defining an ophyd Keithley as an [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html)

I would like to define some structure on my ophyd keithley device so that it can be understood to be an [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html). 

This device currently has no `NX_schema`

```{include} ../_static/examples/example_keithley_1_device.py
:code: python

```

To define some, I'm going to create a new file `Keithely.yaml` in the same directory as where my device definition of `Keithley` is. The definition will map data keys that will be read on the device to their fields in [`NXdetector`](https://manual.nexusformat.org/classes/base_classes/NXdetector.html).

```{include} ../_static/examples/Keithely.yaml
:code: yaml

```

* `$nxclass` is a NeXus attribute which has to come from a constant. It's presence in a level of the schema indicates whether that level is a NeXus group. `bluesky_nexus` provides some light validation against this field using the [defined basemodels](#bluesky_nexus.nx_nexusformat_schema). If you supply an incorrect type, or a required item is missing in the supplied schema, then an error will be raised by the decorator.
* The first four definitions simply map the data keys in the device (minus the name of the instance) to their name in the nexus schema. Since all data keys are added to the structure, it wouldn't be strictly necessary to map these if the data key name were already equal to the name in the nexus structure... This isn't always possible.
* `data` is mapping to the `readback` data key. `readback` is given the same name as the device itself as a datakey, an so the name we use with it "" is.
* {`timestamps_of_datakey`: ""} will give 
* The last four are constant fields for all keithley. If any subclass of this Keithley wanted to override them, then they could in their own schema.

```{include} ../_static/examples/example_keithely_2_device.py
:code: python

```

Now when any instance of `Keithley` is read, `bluesky_nexus` will place the structure into an `NXdetector`. As you can see from the below image (silx viewer), all the data keys we didn't reference in our schema are also present in the NeXus structure.

## Simulated Monochromator
