# `NXData` Linking Explanation

When defining a `NxBaseClass.build("NXdata")` there is some nuance in bluesky-nexus. We want every field to automatically become an [`NXLog`](https://manual.nexusformat.org/classes/base_classes/NXlog.html) with it's timestamps. From the description of NXlog, we would assume that it would be perfectly valid to define an [NXData](https://manual.nexusformat.org/classes/base_classes/NXdata.html) device schema, e.g

``` yaml
$nxclass: NXdata
$axes: ["some_axis_signal1", "some_axis_signal2"]
$signal: "data_signal"
data_signal: "datakey1"
some_axis_signal1: "datakey2"
some_axis_signal2: "datakey3"
```

If `some_axis_signal1`, `some_axis_signal2`, and `data_signal` become `NXlog`, this will still pass validation, however plotters (silx, nexpy, etc) will not understand that the NXlog's data should be plotted.

To get around this, internal links on the devices should be specified instead.

``` yaml
$nxclass: NXdata
$axes: ["some_axis_signal1_link", "some_axis_signal2_link"]
$signal: "data_signal_link"
data_signal: "datakey1"
&data_signal_link: ["data_signal", "value"]
some_axis_signal1: "datakey2"
&some_axis_signal1_link: ["some_axis_signal1", "value"]
some_axis_signal2: "datakey3"
&some_axis_signal2_link: ["some_axis_signal2", "value"]
```

This is a workaround linking the signal and axes into the NXlog value of where the datakey's values will be written. We should establish from the NeXus team whether NXlog _should_ work in this case with NXdata, and if so make issues on silx and nexpy.
