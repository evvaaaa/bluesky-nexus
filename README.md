# bluesky nexus

## Table of contents

- [bluesky nexus](#bluesky-nexus)
  - [Table of contents](#table-of-contents)
  - [Description](#description)
  - [Pydantic schema and model capabilities](#pydantic-schema-and-model-capabilities)
    - [Example of schema yml file](#example-of-schema-yml-file)
  - [Rules concerning definition of a groups, datasets and their attributes in the schema yml file](#rules-concerning-definition-of-a-groups-datasets-and-their-attributes-in-the-schema-yml-file)
  - [Role of the schema with the model](#role-of-the-schema-with-the-model)
    - [Example of model class](#example-of-model-class)
  - [Unit definition strategy](#unit-definition-strategy)
  - [Supported pydantic models](#supported-pydantic-models)
  - [Placeholder mechanism](#placeholder-mechanism)
    - [Placeholder syntax](#placeholder-syntax)
  - [Subscription of devices in the baseline](#subscription-of-devices-in-the-baseline)
  - [Requirements for device classes](#requirements-for-device-classes)
    - [Example of custom device](#example-of-custom-device)
  - [Installation and usage in the context of bluesky container (bluesky deployment)](#installation-and-usage-in-the-context-of-bluesky-container-bluesky-deployment)
  - [Installation and usage outside the bluesky container](#installation-and-usage-outside-the-bluesky-container)
    - [NeXus logging setup](#nexus-logging-setup)
    - [Let the preprocessor append ```NeXus metadata``` to the start document](#let-the-preprocessor-append-nexus-metadata-to-the-start-document)
    - [Let the preprocessor append ```devices metadata``` to the start document](#let-the-preprocessor-append-devices-metadata-to-the-start-document)
    - [Subscribe the callback: NexusWriter](#subscribe-the-callback-nexuswriter)
  - [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
  - [Optional definition of the metadata dictionary in Your script that is transferred to the plan](#optional-definition-of-the-metadata-dictionary-in-your-script-that-is-transferred-to-the-plan)
  - [Cheat sheet for maintenance purposes in context of HZB bluesky deployment](#cheat-sheet-for-maintenance-purposes-in-context-of-hzb-bluesky-deployment)
  - [Context](#context)
  - [License](#license)

## Description

**bluesky_nexus** is a Python library designed to create NeXus file from a Bluesky run. The library generates NeXus file containing two primary groups:

- **NXinstrument Group**: Includes all instruments involved in the run, including baseline instruments.
- **NXcollection Group**: Contains the content of the `start` and `stop` documents generated during the run by the Bluesky Run Engine.

---

## Pydantic schema and model capabilities

This library employs Pydantic schemas to allow for detailed mapping and customization, including:

1. **Component selection and mapping**:
   - Specify which components of a device class are mapped into the NeXus base class.
   - Define mappings between device class component names and NeXus field names (e.g., `en` → `energy`).

2. **Structural mapping**:
   - Map device class component structures to NeXus base class structures (e.g., `mono.grating` → `mono.grating.diffraction_order`).

3. **Value transformation**:
   - Apply conversion formulas to transform component values (e.g., eV to keV)
   - The evaluation of the expression is executed in the restricted environment

4. **NeXus metadata**:
   - Define NeXus base class names (e.g. `NXmonochromator`, `NX_FLOAT`)
   - Define data types of component values mapped into NeXus fields (e.g. `float64`, `int32`, `str`).
   - Specify the unit of component values (e.g., `rad`, `keV`).

5. **Data fetching**:
   - Determine when component values should be fetched:
     - **Pre-run**: Based on static metadata or data read from the instrument available before the run
     - **Post-run**: Based on event documents and descriptors available after the run.

### Example of schema yml file

The following example shows how groups, fields, attrs and attributes can be defined in the schema yml file. This example contains elements that are not applicable in the real case, it is only intended to show the possibilities.

```yaml
nx_model: NXmonochromatorModel # pydantic model associated with this schema
nxclass: NXmonochromator # group: NXmonochromator

energy: # field: "energy" belongs to NXmonochromator group
  nxclass: NX_FLOAT
  value: $post-run:en # fetch it from the device component
  dtype: float64
  attrs:  # attrs belong to field: "energy"
    units: "keV"
    prices: "Euro"
    days: ["Mo", "We"]
    factors: [1.34, 2.78]
    destination: {"departement": "A23"}
    value: 12.34
    PI: 3.1415
    active: [True, False]
  transformation:
    expression: 3 * x**2 + np.exp(np.log(5)) + 1 # symbolic expression for the transformation
    target: value # specifies the name of array to which expression is applied
GRATING:  # group: 'GRATING' belongs to NXmonochromator group
  nxclass: NXgrating
  attrs: # attrs belong to group "GRATING"
    attr_0: "new"
    value: 167
  diffraction_order: # field: "diffraction_order" belongs to group "GRATING"
    nxclass: NX_INT
    value: $pre-run-cpt:grating
    dtype: int32
    attrs: # attrs belong to field "diffraction_order"
      at_0: 13.14
      at_1: [2.03, 4.05]
      value: "some_value"

TRANSFORMATIONS: # group: 'TRANSFORMATIONS' belongs to NXmonochromator group
  nxclass: NXtransformations
  alpha:  # field: "alpha" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:alpha # fetch it from the device component
    dtype: float64
    attributes:
      transformation_type:
        value: $pre-run-md:transformations:alpha:transformation_type # fetch it from the device metadata (happi)
        dtype: str
      units:
        value: $pre-run-md:transformations:alpha:units # fetch it from the device metadata (happi)
        dtype: str
      vector:
        value: $pre-run-md:transformations:alpha:vector # fetch it from the device metadata (happi)
        dtype: int64
      depends_on:
        value: $pre-run-md:transformations:alpha:depends_on # fetch it from the device metadata (happi)
        dtype: str
      description:
        value: $pre-run-md:transformations:alpha:description # fetch it from the device metadata (happi)
        dtype: str
  beta: # field: "beta" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:beta # fetch it from the device component
    dtype: float64
    attributes:
      transformation_type:
        value: $pre-run-md:transformations:beta:transformation_type # fetch it from the device metadata (happi)
        dtype: str
      units:
        value: $pre-run-md:transformations:beta:units # fetch it from the device metadata (happi)
        dtype: str
      vector:
        value: $pre-run-md:transformations:beta:vector # fetch it from the device metadata (happi)
        dtype: int64
      depends_on:
        value: $pre-run-md:transformations:beta:depends_on # fetch it from the device metadata (happi)
        dtype: str
      description:
        value: $pre-run-md:transformations:beta:description # fetch it from the device metadata (happi)
        dtype: str
  theta: # field: "theta" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:theta # fetch it from the device component
    dtype: float64
    attributes:
      transformation_type:
        value: $pre-run-md:transformations:theta:transformation_type # fetch it from the device metadata (happi)
        dtype: str
      units:
        value: $pre-run-md:transformations:theta:units # fetch it from the device metadata (happi)
        dtype: str
      vector:
        value: $pre-run-md:transformations:theta:vector # fetch it from the device metadata (happi)
        dtype: int64
      depends_on:
        value: $pre-run-md:transformations:theta:depends_on # fetch it from the device metadata (happi)
        dtype: str
      description:
        value: $pre-run-md:transformations:theta:description # fetch it from the device metadata (happi)
        dtype: str
  alpha_setpoint: # field: "alpha_setpoint" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:alpha_setpoint # fetch it from the device component
    dtype: float64

  beta_setpoint: # field: "beta_setpoint" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:beta_setpoint # fetch it from the device component
    dtype: float64

  theta_setpoint: # field: "theta_setpoint" belongs to TRANSFORMATIONS group
    nxclass: NX_FLOAT
    value: $post-run:theta_setpoint # fetch it from the device component
    dtype: float64

description: # field: 'description' belongs to NXmonochromator group
  nxclass: NX_CHAR
  value: $pre-run-md:description # fetch it from the device metadata (happi)
  dtype: str
attrs:  # attrs belong to NXmonochromator group
  attr_0: 3.1415
  value: "3.1415"
  attr_1: {'a':'2'}
  attr_2: "{'b':'1'}"
  attr_3: [1.02, 3.04, 5.06]
  attr_4: [5, 6, 7]
  attr_5: True

###
### NXmonochromator group allows extra groups/fields that are not explicitly defined in the model
###
someGroup: # additional group: "someGroup"
  nxclass: NXsomeClass
  attrs:
    attr_1: {"a":"2"}
    attr_2: [5.06, 7.08]
  energy: # field energy belonging to someGroup
    nxclass: NX_FLOAT
    value: $post-run:en
    dtype: float64
    attrs:
      attr_1: "PI"
      attr_2: 3.1415
someDataset: # additional dataset: "someDataset"
  nxclass: NX_FLOAT
  value: $post-run:en
  dtype: float64
```

---

## Rules concerning definition of a groups, datasets and their attributes in the schema yml file

Elements of a group:

- definition of `nxclass`: mandatory. This is a name of the group equivalent to the name of the NeXus base class defining this group. E.g. NXmonochromator, NXgrating, NXtransformations, etc.
- definition of `attributes`: facultative and applicable only if attributes are defined at the group level by the NeXus base class of the group. Attributes at the group level are associated with the group.
- definition of datasets: facultative and applicable as defined by the NeXus base class defining the group
- definition of `attrs`: facultative arbitrary attributes at the group level defined by the user and not by the the NeXus base class of the group. The input is not validated by the pydantic model since not defined by the NeXus base class of the group. Attributes at the group level are associated with the group.

Elements of a dataset:

- definition of `nxclass`: mandatory, defined in the the NeXus base class of the group the dataset belongs to, e.g. NX_FLOAT, NX_INT, NX_CHAR ...
- definition of `value`: mandatory placeholder for addressing the device component from which the data is to be retrieved from bluesky documents once the bluesky run is done.
- definition of `dtype`: obligatory in case the device component does not provide data type information. If device provides data type information the user can still force/overwrite the data type for the dataset to be written to the NeXus file by defining explicitelly the `dtype`, e.g. float64, int32, str, bool ...
- definition of `attributes`: facultative and applicable only if attributes are defined at the dataset level by the NeXus base class of the group the dataset belongs to. Attributes at the dataset level are associated with the dataset.
- definition of `attrs`: facultative, arbitrary attributes at the dataset level defined by the user and not by the the NeXus base class of the group the dataset belongs to. The input is not validated by the pydantic model since it is not defined by the NeXus base class of the group the dataset belongs to. Attributes at the datset level are associated with the dataset.
- definition of `transformation`: applicable if transformation of the numerical value/values provided by the device component is required before writting it/them to the NeXus file.

Elements of `attributes` defined at the group or dataset level:

- `value`: mandatory placeholder for addressing the device component from which the data is to be retrieved from bluesky documents once the bluesky run is done. Instead of the placeholder it can also be a scalar value.
- `dtype`:
  - if `value` defines a placeholder: obligatory in case the device component does not provide data type information. If device provides data type information the user can still force/overwrite the data type for the attribute to be written to the NeXus file by defining explicitelly the `dtype`, e.g. float64, int32, str, bool ...
  - if `value` defines a fixed scalar value: obligatory, i.e. str, float64, int32 ...

The “attrs” defined by the user at group or dataset level are saved in the NeXus file according to the following rules:

- dictionary is converted to a JSON string and saved as variable-length UTF-8 string value
- string is saved as variable-length UTF-8 string value
- integer is saved as int64 value
- float is saved as float64 value
- bool is saved as uint8 value
- list of floats/integers/bools is saved as numpy array of float64/int64/uint8 values

---

## Role of the schema with the model

The schema file specifies how data should be structured and which model should be applied.
This connection is established through the nx_model field in the schema file. For example:

```yaml
nx_model: NXmonochromatorModel
nxclass: NXmonochromator
```

Here, the nx_model field (e.g., NXmonochromatorModel) explicitly defines the model responsible for handling the schema. This mapping ensures that the rules, transformations, and validations specified in the model are applied to the corresponding NeXus group or field. Moreover, the model allows for the inclusion of verbal descriptions of component roles, improving clarity.

### Example of model class

```python
class NXmonochromatorModel(NXgroupModel):

    default: NXattrModel = Field(NXattrModel(value="energy"), description='Default.')
    wavelength: Optional[NXfieldModelWithPrePostRunString] = Field(None, description="Wavelength selected.")
    wavelegth_errors: Optional[NXfieldModelWithPrePostRunString] = Field(None, description="Wavelength standard deviation.")
    energy: Optional[NXfieldModelWithPrePostRunString] = Field(None, description="Energy selected.")
    energy_errors: Optional[NXfieldModelWithPrePostRunString] = Field (None, description="Energy standard deviation.")
    depends_on: Optional[NXfieldModelWithPrePostRunString] = Field(None, description="NeXus positions components by applying a set of translations and rotations.")
    distribution: Optional[NXdataModel] = Field(None, description="Distribution.")
    OFF_GEOMETRY: Optional[NXoff_geometryModel] = Field(None, description='This group describes the shape of the beam line component.')
    CRYSTAL: Optional[NXcrystalModel] = Field(None, description="Use as many crystals as necessary to describe.")
    GRATING: Optional[NXgratingModel] = Field(None, description="For diffraction grating based monochromators.")
    TRANSFORMATIONS: Optional[NXtransformationsModel] = Field(None, description="This is the group recommended for holding the chain of translation and rotation operations necessary to position the component within the instrument.")
    description: Optional[NXfieldModelWithPrePostRunString] = Field(None, description="Description of the monochromator.")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
```

---

## Unit definition strategy

The schema supports defining units for device components. The strategy for defining units in the schema yml file is as follows:

1. **Device provides units**:
   If the device natively returns units, the units provided by the device are used directly. In such a case do not define any `units` under `attrs`, otherwise the `units` defined under `attrs` will be used.

2. **Device does not provide units**:
   If the device does not return any units, define the corresponding unit value in the `units` under `attrs`. This ensures that the correct units are explicitly defined for this specific device.

---

## Supported pydantic models

  List of Pydantic models currently supported:

    - `NXdetectorModel`
    - `NXdetector_groupModel`
    - `NXgeneralModel`
    - `NXmonitorModel`
    - `NXmonochromatorModel`
    - `NXpositionerModel`

---

## Placeholder mechanism

The **bluesky_nexus** library uses placeholders to manage and organize data fetched during different phases of the run. These placeholders are incorporated into the `nexus_md` dictionary in the `start` document and are filled during the pre-run or post-run phases.

### Placeholder syntax

1. **Pre-run metadata**:
   - Fetch metadata associated with a device instance.
   - Syntax: `$pre-run-md:<metadata_name>`
   - Details:
     - The separation between the prefix `$pre-run-md` and metadata name is made by applying the colon sign (`:`).
     - The separation between items of the `<metadata_name>` is also made by applying the colon sign (`:`).
     - **Examples**:
       - `$pre-run-md:grating_substrate_material`
       - `$pre-run-md:worldPosition:x`

2. **Pre-run component values**:
   - Fetch values from components before the run.
   - Syntax: `$pre-run-cpt:<component_name>`
   - Details:
     - The separation between the prefix `$pre-run-cpt` and component name is made by applying the colon sign (`:`).
     - The separation between items of the `<component_name>` is also made by applying the colon sign (`:`).
     - **Examples**:
       - `$pre-run-cpt:grat:diffraction_order`
       - `$pre-run-cpt:en:readback`

3. **Post-run component values**:
   - Retrieve values of components after the run from event documents or descriptor document.
   - Syntax: `$post-run:<component_name>`
   - Details:
     - The separation between the prefix `$post-run` and component name is made by applying the colon sign (`:`).
     - The separation between items of the `<component_name>` is made by applying the underscore sign (`_`) (as per the ophyd naming style).
     - If in the class definition of the component its name is “reduced” to the name of the instance that contains this component, e.g.: `self.readback.name = self.name`, this must be taken into account when defining the character string that appears after `$post-run`.
     - **Examples**:
       - `$post-run:grating_diffraction_order`
       - `$post-run:en`
       - `$post-run`

    The data of device components with `kind='config'` are retrieved from the `configuration` dictionary of the descriptor document.
    The data of device components with `kind='hinted'` or `kind='normal'` are retrieved from the `data_keys` dictionary of the descriptor document and from the associated events documents.
    As far as the sequence is concerned, the data is retrieved from the stream descriptors. Only if the component name could not be found in the stream descriptors is the data retrieved from the baseline descriptor.

---

## Subscription of devices in the baseline

  If only some but not all of the components of a device used in the schema yml file are used in a plan, subscribe the device in the baseline so that the device components not used in the plan can be found in the baseline descriptor, allowing replacement of all the placeholders defined in the schema yml file associated with the device.

---

## Requirements for device classes

All device classes must be decorated by the `NxSchemaLoader`. The role of the decorator is to associate the pydantic nexus schema with the device class. The decorator expects a string variable as a parameter, which stores the pydantic schema in the form of a yml string. This requirement ensures that each device instance is correctly configured for NeXus data handling. The definition of the `NxSchemaLoader` decorator is located at: `bluesky_nexus/src/bluesky_nexus/common/decorator_utils.py`.

The pydantic schemas in the form of a yml strings are stored in the python files. The name of the variable that stores the yml string should be defined in such a way that the device class for which this variable is defined can be easily identified. For a device class with the name “Mono”, the name of the variable that saves the schema yml string could be “Mono_nxschema”, for example. See the example below:

### Example of custom device

To define a custom device, create a class that inherits from the `Device` class and decorate it with the `NxSchemaLoader` decorator. Pass the pydantic nexus schema to the decorator in the form of a yml string. This ensures that the device is correctly associated with its corresponding NeXus pydantic schema.

```python
NxSchemaLoader(Mono_nxschema)
class Mono(Device):
    en: SynAxis = Cpt(SynAxis, name="en")
    grating: Signal = Cpt(Signal, name="grating")
    slit: Signal = Cpt(Signal, name="slit")
```

---

## Installation and usage in the context of bluesky container (bluesky deployment)

  Make sure that the “nexus.py” file is located in the “beamline_config” directory. The content of “nexus.py” is:

```python
from .base import *
from .beamline import *

from bluesky_nexus.preprocessors.supplemental_metadata import SupplementalMetadata
from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import setup_nx_logger, LogLevel
from bluesky_nexus.bluesky_nexus_paths import (
    get_nx_file_dir_path,
    get_nx_log_file_dir_path,
)

# This is an optional setup for the NeXus logger. If not configured, logging to a file
# is disabled by default. The logger supports separate configuration for console and
# file output, with options for log rotation, formatting, and enabling/disabling handlers.
nx_log_file_dir_path: str = get_nx_log_file_dir_path()
setup_nx_logger(
    console_level=LogLevel.ERROR,
    file_level=LogLevel.DEBUG,
    log_file_dir_path=nx_log_file_dir_path,
    log_file_name="nx_log.log",
    log_format=None,  # Uses default format if None
    max_file_size=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    enable_console=True,
    enable_file=True,
)

# Note: `SupplementalMetadata` accepts `devices_dictionary` and `md_type` either as positional or keyword arguments.
# For clarity, keyword arguments are recommended.

# Let the preprocessor append NeXus metadata to the start document

# using keyword arguments (recommended)
metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.NEXUS_MD)
# or using positional arguments
metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.NEXUS_MD)
RE.preprocessors.append(metadata)


# Let the preprocessor append devices metadata to the start document

# using keyword arguments (recommended)
metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.DEVICE_MD)
# or using positional arguments
metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.DEVICE_MD)
RE.preprocessors.append(metadata)

# Subscribe the callback: 'NexusWriter'
nx_file_dir_path: str = get_nx_file_dir_path()
cpt_name_delimiter: str = "_" # Optionally specify a delimiter used in Bluesky documents to separate device components. If not specified, the default is "_".
nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path, cpt_name_delimiter = cpt_name_delimiter)
RE.subscribe(nexus_writer)
```

See the section [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
on the optional NeXus logger below for detailed information on each parameter
of the optional NeXus logger setup.

Make sure that the file `__init__.py` in the “beamline_config” directory contains the following import:

```python
from .nexus import *
```

---

## Installation and usage outside the bluesky container

- Clone the main branch of the project [bluesky_nexus](https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bluesky_nexus)
- Create and activate an environemet with python_version >= "3.10"
- Install bluesky_nexus package in this environement.

  If you are working in a production environment use:

  ```bash
  cd "path to cloned `bluesky_nexus` package"
  pip install .
  ```

  If you are working in a development environment use:

  ```bash
  cd "path to cloned `bluesky_nexus` package"
  pip install -e .
  ```

  In your script use following imports:

  ```python
  from bluesky_nexus.preprocessors.supplemental_metadata import SupplementalMetadata
  from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
  from bluesky_nexus.common.logging_utils import setup_nx_logger, LogLevel
  ```

Add the following NeXus logging setup, preprocessor, and callback subscriptions to your script:

### NeXus logging setup

This is an optional setup for the NeXus logger. If not configured, logging to a file
is disabled by default. The logger supports separate configuration for console and
file output, with options for log rotation, formatting, and enabling/disabling handlers.

See the section [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
on the optional NeXus logger below for detailed information on each parameter
of the optional NeXus logger setup.

```python
nx_log_file_dir_path: str = "Your path to the NeXus log file directory"
setup_nx_logger(
    console_level=LogLevel.ERROR,
    file_level=LogLevel.DEBUG,
    log_file_dir_path=nx_log_file_dir_path,
    log_file_name="nx_log.log",
    log_format=None,  # Uses default format if None
    max_file_size=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    enable_console=True,
    enable_file=True,
)
```

### Let the preprocessor append ```NeXus metadata``` to the start document

**Note:** `SupplementalMetadata` accepts `devices_dictionary` and `md_type` either as positional or keyword arguments.
For clarity, keyword arguments are recommended.

In you script subscribe to the preprocessor

  ```python
  # Let the preprocessor append NeXus metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.NEXUS_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.NEXUS_MD)
  RE.preprocessors.append(metadata)
  ```

### Let the preprocessor append ```devices metadata``` to the start document

In you script subscribe to the preprocessor

  ```python
  # Let the preprocessor append devices metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.DEVICE_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.DEVICE_MD)
  RE.preprocessors.append(metadata)
  ```

### Subscribe the callback: NexusWriter

In you script subscribe to the callback

  ```python
  nx_file_dir_path: str = "Your path to nx_file directory"
  cpt_name_delimiter: str = "_" # Optionally specify a delimiter used in Bluesky documents to separate device components. If not specified, the default is "_".
  nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path, cpt_name_delimiter = cpt_name_delimiter)
  RE.subscribe(nexus_writer)
  ```

---

## Explanations on the optional NeXus logger

- Adjust the log levels for console and file output using `console_level` and `file_level` if necessary.
  - These accept values from the `LogLevel` enum:
    - `LogLevel.DEBUG`
    - `LogLevel.INFO`
    - `LogLevel.WARNING`
    - `LogLevel.ERROR`
    - `LogLevel.CRITICAL`
  - Default values:
    - `console_level` = `LogLevel.ERROR`
    - `file_level` = `LogLevel.DEBUG`

- Adjust the custom log format using `log_format` if necessary.
  - If not specified, the default format is used:

    ```python
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s  %(message)s"
    ```

- Adjust the maximum size of a log file (in bytes) before rotation occurs using `max_file_size` if necessary.
  - Default value: `max_file_size` = `10 * 1024 * 1024` (10 MB)

- Adjust the number of backup log files to keep after rotation using `backup_count`.
  - Default value: `backup_count` = `5`

- Enable or disable logging to the console or file using `enable_console` and `enable_file`.
  - Both default to `True`.

- File logging requires a valid path in `log_file_dir_path` **and a defined `log_file_name`.**
  - If `log_file_dir_path` is `None` or `enable_file=False`, file logging is disabled.
  - Default value for `log_file_name` is `"nx_log.log"`, but it must be explicitly provided when customizing file logging behavior.

---

## Optional definition of the metadata dictionary in Your script that is transferred to the plan

  ```python
  md = {
      "nx_file_name": "test_{uid}",  # Facultative
      "title": "fast test at HZB",  # Facultative
      "definition": "NXxas",  # Facultative
      }
  ```

The 'nx_file_name' enables the creation of a user-defined name for the NeXus file. If it is not defined, the name of the NeXus file is generated automatically based on
the 'uid' extracted from the start document of the run (start_doc[“uid”]). You can use ```{uid}``` in the user-defined name (as in the example above), which is replaced by the uid extracted from the run's start document (start_doc[“uid”]).

  ```python
  def my_plan():
    yield from scan(detectors, motor, 1, 10, 5, md=md)
  ```

---

## Cheat sheet for maintenance purposes in context of HZB bluesky deployment

  The file "~/.bluesky-deployment/bluesky-container/run_bluesky.sh" has to contain following volume mounts and environment variable setting:

  ```bash
  -v ${NX_FILE_DIR_PATH}:${_NX_FILE_DIR_PATH} \
  -v ${NX_LOG_FILE_DIR_PATH}:${_NX_LOG_FILE_DIR_PATH} \
  ```

  ```bash
  --env _NX_FILE_DIR_PATH=${_NX_FILE_DIR_PATH} \
  --env _NX_LOG_FILE_DIR_PATH=${_NX_LOG_FILE_DIR_PATH} \
  ```

  The file "/etc/environement" has to contain following definitions of env. variables:

  ```bash
NX_FILE_DIR_PATH=/home/daniel/bluesky/data/nexus/file
_NX_FILE_DIR_PATH=/opt/bluesky/nx_file_dir
NX_LOG_FILE_DIR_PATH=/home/daniel/bluesky/data/nexus/log
_NX_LOG_FILE_DIR_PATH=/opt/bluesky/nx_log_file_dir
  ```

Replace in the paths `daniel` by a username.

---

## Context

This package was developed as part of the activities of the WP2 group of the Helmholtz-founded project **ROCK-IT** (Remote, Operando Controlled, Knowledge-driven, and IT-based).

---

## License

This project is licensed under the terms specified in the [License](./LICENSE) file.
