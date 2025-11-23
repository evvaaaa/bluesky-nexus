# bluesky nexus

## Table of contents

- [bluesky nexus](#bluesky-nexus)
  - [Table of contents](#table-of-contents)
  - [Description](#description)
  - [Operating Modes](#operating-modes)
  - [Architecture overview (service mode)](#architecture-overview-service-mode)
  - [Command-line usage (service mode)](#command-line-usage-service-mode)
    - [Quick start: ZMQ mode](#quick-start-zmq-mode)
    - [Quick start: Kafka mode](#quick-start-kafka-mode)
    - [Help](#help)
  - [CLI Logging Options (service mode)](#cli-logging-options-service-mode)
  - [ZMQ backend options](#zmq-backend-options)
    - [ZMQ Backend Options](#zmq-backend-options-1)
  - [Kafka backend options](#kafka-backend-options)
    - [Kafka Backend Options](#kafka-backend-options-1)
  - [Ophyd component name delimiter](#ophyd-component-name-delimiter)
    - [CLI](#cli)
    - [Environment variable](#environment-variable)
  - [Directory validation requirements](#directory-validation-requirements)
  - [Environment variables overview (complete reference)](#environment-variables-overview-complete-reference)
    - [Logging Environment Variables (Shared)](#logging-environment-variables-shared)
    - [ZMQ Backend Environment Variables](#zmq-backend-environment-variables)
    - [Kafka Backend Environment Variables](#kafka-backend-environment-variables)
  - [Pydantic schema and model capabilities](#pydantic-schema-and-model-capabilities)
    - [Example of schema yml file](#example-of-schema-yml-file)
  - [Rules concerning definition of a groups, datasets and their attributes in the schema yml file](#rules-concerning-definition-of-a-groups-datasets-and-their-attributes-in-the-schema-yml-file)
    - [Group](#group)
    - [Dataset](#dataset)
    - [Group \& Dataset — Definition of Attributes and Attrs](#group--dataset--definition-of-attributes-and-attrs)
  - [Role of the schema with the model](#role-of-the-schema-with-the-model)
    - [Example of model class](#example-of-model-class)
  - [Unit definition strategy](#unit-definition-strategy)
  - [Supported pydantic models](#supported-pydantic-models)
  - [Placeholder mechanism](#placeholder-mechanism)
    - [Placeholder syntax](#placeholder-syntax)
  - [Subscription of devices in the baseline](#subscription-of-devices-in-the-baseline)
  - [Requirements for device classes](#requirements-for-device-classes)
    - [Example of custom device](#example-of-custom-device)
  - [Installation and usage in the context of bluesky container (embedded NexusWriter mode)](#installation-and-usage-in-the-context-of-bluesky-container-embedded-nexuswriter-mode)
  - [Installation and usage when NexusWriter runs as a separate service](#installation-and-usage-when-nexuswriter-runs-as-a-separate-service)
    - [How it works](#how-it-works)
  - [Running the Docker container](#running-the-docker-container)
  - [Using start\_bluesky\_nexus\_container.sh](#using-start_bluesky_nexus_containersh)
  - [Installation and usage outside the HZB deployment infrastructure](#installation-and-usage-outside-the-hzb-deployment-infrastructure)
    - [Installation](#installation)
    - [Operating Modes](#operating-modes-1)
      - [Mode A – Local mode (NexusWriter in the same process as the RE)](#mode-a--local-mode-nexuswriter-in-the-same-process-as-the-re)
      - [Mode B – Remote mode (NexusWriter executed as a separate process)](#mode-b--remote-mode-nexuswriter-executed-as-a-separate-process)
  - [NeXus directory structure](#nexus-directory-structure)
  - [NeXus file naming conventions](#nexus-file-naming-conventions)
    - [Case 1 — User provides `nx_file_name`](#case-1--user-provides-nx_file_name)
    - [Case 2 — User does not provide `nx_file_name` (or value is empty)](#case-2--user-does-not-provide-nx_file_name-or-value-is-empty)
      - [Auto-generated filename format](#auto-generated-filename-format)
      - [Example](#example)
  - [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
  - [Cheat sheet for maintenance purposes in context of HZB bluesky deployment](#cheat-sheet-for-maintenance-purposes-in-context-of-hzb-bluesky-deployment)
  - [Context](#context)
  - [License](#license)

## Description

**bluesky_nexus** is a Python library designed to create NeXus file from a Bluesky run. The library generates NeXus file containing two primary groups:

- **NXinstrument Group**: Includes all instruments involved in the run, including baseline instruments.
- **NXcollection Group**: Contains the content of the `start` and `stop` documents generated during the run by the Bluesky Run Engine.

---

## Operating Modes

The bluesky_nexus package can be used in two different execution modes:

1. Embedded mode (non-service mode)

   - NexusWriter runs in the same process as the RunEngine (RE).
   - No ZeroMQ or Kafka required.
   - The NexusWriter callback is added directly to the RE via RE.subscribe(...).
   - NeXus files are written synchronously within the RE process.
   - Suitable for local development, test setups, or simple beamlines.

    See: [Installation and usage in the context of bluesky container (embedded NexusWriter mode)](#installation-and-usage-in-the-context-of-bluesky-container-embedded-nexuswriter-mode)

2. Service mode (NexusWriter running in a dedicated container or Python process)

   - The main RE publishes Bluesky documents over ZeroMQ or Kafka.
   - A remote RemoteDispatcher receives documents and writes NeXus files.
   - The NexusWriter runs independently from the RE, increasing stability.

    See: [Installation and usage when NexusWriter runs as a separate service](#installation-and-usage-when-nexuswriter-runs-as-a-separate-service)

---

## Architecture overview (service mode)

When running the NexusWriter as a separate service (instead of embedding it inside your Bluesky RunEngine), the system follows a simple and robust architecture:

```java
RunEngine (RE)
     │
     ├── publishes Bluesky documents
     │      • ZMQ Publisher (port 5577 → 5578 via proxy)
     │      • OR Kafka Publisher (topic: bluesky.documents)
     │
ZeroMQ Proxy or Kafka Broker
     │
RemoteDispatcher (ZMQ or Kafka)
     │
NexusWriter
     │
HDF5/NeXus file (.nxs)
```

Key idea:
The NexusWriter runs in a separate, long-running background process (container).
It listens for Bluesky documents published by the RE and writes NeXus files independently.

This provides:

- Isolation between data acquisition and file writing
- Reliability (crashes in writer do not affect RE)
- Flexibility (can switch between ZMQ and Kafka backends)

---

## Command-line usage (service mode)

The bluesky_nexus package exposes a complete command-line interface through:

```bash
python -m bluesky_nexus
```

It supports:

- Top-level logging configuration
- Subcommands:
  - zmq – read Bluesky documents via ZeroMQ
  - kafka – read Bluesky documents from Kafka

General syntax:

```bash
python -m bluesky_nexus [LOGGING OPTIONS] <zmq|kafka> [BACKEND OPTIONS]
```

⚠️ Important:

All logging-related options must appear before the backend (zmq or kafka) on the command line.

### Quick start: ZMQ mode

```bash
python -m bluesky_nexus \
    --log-dir /home/user/nexus_logs \
    zmq \
        --zmq-ip localhost \
        --zmq-port 5578 \
        --nx-dir /home/user/nexus_output
```

### Quick start: Kafka mode

```bash
python -m bluesky_nexus \
    --log-dir /home/user/nexus_logs \
    kafka \
        --kafka-brokers localhost:9092 \
        --kafka-topic bluesky.documents \
        --nx-dir /home/user/nexus_output
```

### Help

```bash
python -m bluesky_nexus --help
python -m bluesky_nexus zmq --help
python -m bluesky_nexus kafka --help
```

---

## CLI Logging Options (service mode)

The service provides a full-featured logging system with log rotation, file/console levels, and environment variable overrides.

These options **must be placed before the backend command** (`zmq` or `kafka`).

| CLI Argument     | Environment Variable      | Default        | Description                              |
|------------------|---------------------------|----------------|------------------------------------------|
| `--log-dir`      | `_NX_LOG_FILE_DIR_PATH`   | required       | Directory where log files are written.   |
| `--console-level`| `_NX_CONSOLE_LOG_LEVEL`   | `ERROR`        | Console log level.                       |
| `--file-level`   | `_NX_FILE_LOG_LEVEL`      | `DEBUG`        | File log level.                          |
| `--log-file-name`| `_NX_LOG_FILE_NAME`       | `nx_log.log`   | Name of the main log file.               |
| `--file-max-size`| `_NX_LOG_FILE_MAX_SIZE`   | `10MB`         | Maximum log size before rotation.        |
| `--backup-count` | `_NX_BACKUP_COUNT`        | `5`            | Number of rotated logs to keep.          |
| `--enable-console`| `_NX_ENABLE_CONSOLE_LOG` | `True`         | Enable console logging.                  |
| `--enable-file`  | `_NX_ENABLE_FILE_LOG`     | `True`         | Enable file logging.                     |

Example:

```bash
python -m bluesky_nexus \
    --log-dir /tmp/nexus_logs \
    --console-level INFO \
    --file-level DEBUG \
    kafka \
        --kafka-brokers localhost:9092 \
        --kafka-topic bluesky.documents \
        --nx-dir /tmp/nexus_output
```

---

## ZMQ backend options

These options apply when invoking:

```bash
python -m bluesky_nexus zmq ...

```

### ZMQ Backend Options

| CLI Argument      | Environment Variable            | Description                        |
|-------------------|---------------------------------|------------------------------------|
| `--zmq-ip`        | `_ZMQ_IP`                       | ZeroMQ publisher IP.               |
| `--zmq-port`      | `_ZMQ_PORT`                     | ZeroMQ publisher port.             |
| `--nx-dir`        | `_NX_FILE_DIR_PATH`             | Output directory for NeXus files.  |
| `--cpt-delimiter` | `_OPHYD_CPT_NAME_DELIMITER`     | Ophyd cpt delimiter                |

ZeroMQ Networking Notes

HZB setup:

- RE publishes to port 5577
- ZMQ proxy forwards 5577 → 5578
- NexusWriter connects to 5578

To run the proxy see chapter TO DO:  put a LINK

---

## Kafka backend options

Used when invoking:

```bash
python -m bluesky_nexus kafka ...
```

### Kafka Backend Options

| CLI Argument        | Environment Variable            | Description                                 |
|---------------------|---------------------------------|---------------------------------------------|
| `--kafka-brokers`   | `_KAFKA_BROKERS`                | Bootstrap server list (`host:port`).        |
| `--kafka-topic`     | `_KAFKA_TOPIC`                  | Topic containing Bluesky documents.         |
| `--kafka-group`     | `_KAFKA_GROUP`                  | Consumer group ID (default `"default"`).    |
| `--nx-dir`          | `_NX_FILE_DIR_PATH`             | Output directory for NeXus files.           |
| `--cpt-delimiter`   | `_OPHYD_CPT_NAME_DELIMITER`     | Ophyd delimiter.                            |

Notes on Kafka usage:

- Consumer group defines delivery semantics
  - Same group → load balancing
  - Different group → independent consumers
- Each message corresponds to a Bluesky document dict (start, descriptor, event, stop).
- The NexusWriter subscribes internally via the Kafka dispatcher.

---

## Ophyd component name delimiter
Ophyd devices can use different naming conventions of components/signals depending on if they are ophyd pure or ophyd-async devices.

### CLI

```bash
--cpt-delimiter "-"

```

### Environment variable

```ini
_OPHYD_CPT_NAME_DELIMITER="-"
```

If not provided, a default: '_' is used.

---

## Directory validation requirements
The CLI validates:

- Log directory (--log-dir)
- NeXus output directory (--nx-dir)

Validation behavior:

- Directory must exist before running
- If missing → ValueError is raised

---

## Environment variables overview (complete reference)

### Logging Environment Variables (Shared)

| Environment Variable        | Description                  |
|-----------------------------|------------------------------|
| `_NX_LOG_FILE_DIR_PATH`     | Directory for log files.     |
| `_NX_LOG_FILE_NAME`         | Log filename.                |
| `_NX_LOG_FILE_MAX_SIZE`     | Max size before rotating.    |
| `_NX_BACKUP_COUNT`          | Number of rotated logs.      |
| `_NX_CONSOLE_LOG_LEVEL`     | Console logging level.       |
| `_NX_FILE_LOG_LEVEL`        | File logging level.          |
| `_NX_ENABLE_CONSOLE_LOG`    | Enable console logging.      |
| `_NX_ENABLE_FILE_LOG`       | Enable file logging.         |

### ZMQ Backend Environment Variables

| Environment Variable            | Description                        |
|---------------------------------|------------------------------------|
| `_ZMQ_IP`                       | Publisher IP.                      |
| `_ZMQ_PORT`                     | Publisher port.                    |
| `_NX_FILE_DIR_PATH`             | Output directory for NeXus files.  |
| `_OPHYD_CPT_NAME_DELIMITER`     | Ophyd delimiter.                   |

### Kafka Backend Environment Variables

| Environment Variable            | Description                                 |
|---------------------------------|---------------------------------------------|
| `_KAFKA_BROKERS`                | Kafka bootstrap servers.                    |
| `_KAFKA_TOPIC`                  | Kafka topic.                                |
| `_KAFKA_GROUP`                  | Consumer group (default: `"default"`).      |
| `_NX_FILE_DIR_PATH`             | Output directory for NeXus files.           |
| `_OPHYD_CPT_NAME_DELIMITER`     | Ophyd delimiter.                            |

---

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

### Group

**Elements of a group:**

- **`nxclass`** — **mandatory**: Name of the group equivalent to the name of the NeXus base class defining this group. E.g. NXmonochromator, NXgrating, NXtransformations, etc.
- **`attributes`** — *facultative*: applicable only if attributes are defined at the group level by the NeXus base class of the group. Attributes at the group level are associated with the group.
- **datasets** — *facultative*: applicable as defined by the NeXus base class defining the group
- **`attrs`**: *facultative*: arbitrary attributes at the group level defined by the user and not by the the NeXus base class of the group. The input is not validated by the pydantic model since not defined by the NeXus base class of the group. Attributes at the group level are associated with the group.

### Dataset

The name of a field/dataset should correspond to the **name defined in the NeXus base class** of the group it belongs to.
For example:

- `energy` in case of `NXmonochromator`
- `value` in case of `NXpositioner`

**Elements of a dataset:**

- **`nxclass`** — **mandatory**: Defined in the the NeXus base class of the group the dataset belongs to, e.g. NX_FLOAT, NX_INT, NX_CHAR ...
- **`value`** — **mandatory**: Placeholder for addressing the device component from which the data is to be retrieved from bluesky documents once the bluesky run is done.
- **`dtype`** — **mandatory** in case the device component does not provide data type information. If device provides data type information the user can still force/overwrite the data type for the dataset to be written to the NeXus file by defining explicitly the `dtype`, e.g. float64, int32, str, bool ...
- **`attributes`** — *facultative*: Applicable only if attributes are defined at the dataset level by the NeXus base class of the group the dataset belongs to. Attributes at the dataset level are associated with the dataset.
- **`attrs`** — *facultative*: Arbitrary attributes at the dataset level defined by the user and not by the the NeXus base class of the group the dataset belongs to. The input is not validated by the pydantic model since it is not defined by the NeXus base class of the group the dataset belongs to. Attributes at the dataset level are associated with the dataset.
- **`transformation`** — *facultative*: Applicable if transformation of the numerical value/values provided by the device component is required before writing it/them to the NeXus file.

### Group & Dataset — Definition of Attributes and Attrs

**Elements of `attributes`** defined at the group or dataset level:

- `value`: **mandatory**: Placeholder for addressing the device component from which the data is to be retrieved from bluesky documents once the bluesky run is done. Instead of the placeholder it can also be a scalar value.
- `dtype`:
  - if `value` defines a placeholder: **mandatory** in case the device component does not provide data type information. If device provides data type information the user can still force/overwrite the data type for the attribute to be written to the NeXus file by defining explicitly the `dtype`, e.g. float64, int32, str, bool ...
  - if `value` defines a fixed scalar value: **mandatory**, i.e. str, float64, int32 ...

**Elements of `attrs`** defined by the user at group or dataset level are saved in the NeXus file according to the following rules

- A **dictionary** is converted to a JSON string and saved as variable-length UTF-8 string value.
- A **string** is saved as variable-length UTF-8 string value.
- An **integer** is saved as `int64` value.
- A **float** is saved as `float64` value
- A **bool** is saved as `uint8` value
- A **list** of floats, integers or booleans is saved as NumPy array of `float64`, `int64`, or `uint8` values, respectively.

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

## Installation and usage in the context of bluesky container (embedded NexusWriter mode)

  This mode corresponds to deployment method where the `NexusWriter` is not executed as a separate service.

  Instead, it is instantiated directly inside the `bluesky_container` running the `RunEngine` (RE).
  NeXus files are therefore written from within the same process that runs the RE.

  In the [nexus.py](https://codebase.helmholtz.cloud/hzb/bluesky/beamlines_endstations/vanilla_beamline/source/beamlinetools/-/blob/develop/beamlinetools/beamline_config/nexus.py?ref_type=heads):

- Add imports

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
   ```

- Add optional NeXus logging setup

  ```python
  # This is an optional setup for the NeXus logger. If not configured, logging to a file
  # is disabled by default. The logger supports separate configuration for console and
  # file output, with options for log rotation, formatting, and enabling/disabling handlers
  nx_log_file_dir_path: str = get_nx_log_file_dir_path()
  setup_nx_logger(
      console_level=LogLevel.ERROR,
      file_level=LogLevel.DEBUG,
      log_file_dir_path=nx_log_file_dir_path,
      log_file_name="nx_log.log",
      log_format=None,  # Uses default format if None
      log_file_max_size=10 *1024* 1024,  # 10 MB
      backup_count=5,
      enable_console=True,
      enable_file=True,
  )
  ```

  See the section [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
  for detailed information on the logger configuration.

- Add NeXus metadata to the start document

  ```python
  # Note: `SupplementalMetadata` accepts `devices_dictionary` and `md_type` either as positional or keyword arguments
  # For clarity, keyword arguments are recommended

  # Let the preprocessor append NeXus metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.NEXUS_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.NEXUS_MD)
  RE.preprocessors.append(metadata)
  ```

- Add device metadata to the start document

  ```python
  # Let the preprocessor append devices metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.DEVICE_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.DEVICE_MD)
  RE.preprocessors.append(metadata)
  ```

- Subscribe the NexusWriter

  ```python
  # Subscribe the callback: 'NexusWriter'
  nx_file_dir_path: str = get_nx_file_dir_path()
  cpt_name_delimiter: str = "*" # Optionally specify a delimiter used in Bluesky documents to separate device components. If not specified, the default is "*".
  nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path, cpt_name_delimiter = cpt_name_delimiter)
  RE.subscribe(nexus_writer)
  ```

Please ensure that the file [init.py](https://codebase.helmholtz.cloud/hzb/bluesky/beamlines_endstations/vanilla_beamline/source/beamlinetools/-/blob/develop/beamlinetools/beamline_config/__init__.py?ref_type=heads#L7) file contains:

```python
from .nexus import *
```

This completes the installation and usage in the context of bluesky container (embedded NexusWriter mode)

---

## Installation and usage when NexusWriter runs as a separate service

  This mode corresponds to the deployment method where the `NexusWriter` is
  executed as a separate service.

  It is not instantiated inside the `bluesky_container` running the `RunEngine`. Instead,
  it is instantiated in a standalone background service, a dedicated container.
  NeXus files are therefore written from a different process than the one executing RE.

### How it works

  1. The Bluesky RE process publishes bluesky documents over ZeroMQ. The publication mechanism is implemented in: [base.py](https://codebase.helmholtz.cloud/hzb/bluesky/beamlines_endstations/vanilla_beamline/source/beamlinetools/-/blob/develop/beamlinetools/beamline_config/base.py?ref_type=heads#L26-35).

  2. A ZeroMQ proxy service must be running, forwarding documents from input port 5577 to output 5578. It can be started using:

      ```bash
      docker run -d --rm --name bluesky_zmq --network host \
      registry.hzdr.de/hzb/bluesky/core/images/bluesky_container:v1.4.2 \
      bluesky-0MQ-proxy 5577 5578
      ```

      or

      ```bash
      docker run -d --rm --name bluesky_zmq --network host \
      registry.hzdr.de/hzb/bluesky/core/images/zmq-proxy:1-0-0 \
      bluesky-0MQ-proxy 5577 5578
      ```

  4. The NexusWriter service container must be running. It can be started using:

      ```bash
      TODO
      ```

      The NexusWriter service container  starts a python script "scripts/start_bluesky_nexus_writer_dispatcher.py" when the container is launched.

      The script:
      - instantiates a `RemoteDispatcher` listening on port 5578,
      - registers a `NexusWriter` callback inside this separate process,
      - starts the `RemoteDispatcher` so that documents received on port 5578 can be processed by the `NexusWriter`.

  Important: Since the `NexusWriter` runs in a separate process,  please ensure that the [nexus.py](https://codebase.helmholtz.cloud/hzb/bluesky/beamlines_endstations/vanilla_beamline/source/beamlinetools/-/blob/develop/beamlinetools/beamline_config/nexus.py?ref_type=heads) file does not contain any direct instantiation of `NexusWriter`.

  Remove the following code entirely:

  ```python
  from bluesky_nexus.bluesky_nexus_paths import get_nx_file_dir_path
  from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter

  nx_file_dir_path: str = get_nx_file_dir_path()
  cpt_name_delimiter: str = "_"
  nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path, cpt_name_delimiter=cpt_name_delimiter)
  RE.subscribe(nexus_writer)
  ```

  In this architecture, the subscription is handled exclusively by the NexusWriter service container, not by the main RE process.

  This completes the installation and usage when NexusWriter runs as a separate service.

---

## Running the Docker container
The provided Dockerfile builds a self-contained service:

- Includes the full bluesky_nexus package
- Contains both ZMQ and Kafka backends
- Defines entrypoint:

```dockerfile
ENTRYPOINT ["python", "-m", "bluesky_nexus"]
CMD ["zmq"]

```

Thus:

```bash
docker run bluesky_nexus_writer
```

expands to :

```bash
python -m bluesky_nexus zmq
```

Mounting volumes

```bash
docker run \
   -v /host/data:/data \
   -v /host/logs:/logs \
   bluesky_nexus_writer
```

Important for permissions.
To avoid log files being owned by root:

```bash
--user "$(id -u)":"$(id -g)"
```

---

## Using start_bluesky_nexus_container.sh
The provided script automates:

- Environment variable configuration
- Directory creation
- Backend selection (DISPATCHER_MODE="zmq" or "kafka")
- Container replacement
- Volume mounting
- Host-networking
- Running with correct UID/GID

Usage

```bash
chmod +x scripts/start_bluesky_nexus_container.sh
./scripts/start_bluesky_nexus_container.sh

```

Customizing directories inside the script:

```bash
HOST_DATA_DIR="$HOME/nexus_output"
HOST_LOG_DIR="$HOME/nexus_logs"

```

Backend selection

```bash
DISPATCHER_MODE="zmq"
```

or

```bash
DISPATCHER_MODE="kafka"
```

---

## Installation and usage outside the HZB deployment infrastructure

To use bluesky_nexus outside the HZB Bluesky deployment environment, begin by installing the package manually and then choose one of two operating modes:

- Mode A: NexusWriter runs in the same process as the RunEngine (RE)
- Mode B: NexusWriter runs in a separate process, communicating via ZeroMQ

Both setups are documented below.

### Installation

- Clone the main branch of the project [bluesky_nexus](https://codebase.helmholtz.cloud/hzb/bluesky/core/source/bluesky_nexus)
- Create and activate an environment with python_version >= "3.10"
- Install bluesky_nexus package in this environment:

  Production-style installation

  ```bash
  cd "path/to/cloned/bluesky_nexus"
  pip install .
  ```

  Development installation

  ```bash
  cd "path/to/cloned/bluesky_nexus"
  pip install -e .[dev]
  ```

### Operating Modes

#### Mode A – Local mode (NexusWriter in the same process as the RE)
  (No ZeroMQ required)

  In this mode, the NexusWriter runs inside the same Python process as your RunEngine.
  This is the simplest setup for local experiments or development work.

  In your script:

- Add imports

  ```python
  from bluesky_nexus.preprocessors.supplemental_metadata import SupplementalMetadata
  from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
  from bluesky_nexus.common.logging_utils import setup_nx_logger, LogLevel
  ```

- Add optional NeXus logging setup

    ```python
    nx_log_file_dir_path: str = "Your path to the NeXus log file directory"
    setup_nx_logger(
        console_level=LogLevel.ERROR,
        file_level=LogLevel.DEBUG,
        log_file_dir_path=nx_log_file_dir_path,
        log_file_name="nx_log.log",
        log_format=None,  # Uses default format if None
        log_file_max_size=10 * 1024 * 1024,  # 10 MB
        backup_count=5,
        enable_console=True,
        enable_file=True,
    )
    ```

    See the section [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
    for detailed information on the logger configuration.

- Add NeXus metadata to the start document

    ```python
    # Let the preprocessor append NeXus metadata to the start document

    # using keyword arguments (recommended)
    metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.NEXUS_MD)
    # or using positional arguments
    metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.NEXUS_MD)
    RE.preprocessors.append(metadata)
    ```

- Add device metadata to the start document

  ```python
  # Let the preprocessor append devices metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.DEVICE_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.DEVICE_MD)
  RE.preprocessors.append(metadata)
  ```

- Subscribe the NexusWriter

  ```python
  nx_file_dir_path: str = "Your/path/to/nx_file/directory"
  cpt_name_delimiter: str = "_" # Optionally specify a delimiter used in Bluesky documents to separate device components. If not specified, the default is "_".
  nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path, cpt_name_delimiter = cpt_name_delimiter)
  RE.subscribe(nexus_writer)
  ```

  This completes the embedded/local mode setup.

#### Mode B – Remote mode (NexusWriter executed as a separate process)
  (ZeroMQ required)

  In this mode, the NexusWriter is not instantiated in your experiment script.
  Instead, it runs in a separate container. This process listens to a ZeroMQ proxy that forwards Bluesky documents from the RE.

- Start a ZeroMQ proxy to forward documents from input port: 5577 to output port: 5578

  ```bash
  docker run -d --rm --name bluesky_zmq --network host \
  registry.hzdr.de/hzb/bluesky/core/images/zmq-proxy:1-0-0 \
  bluesky-0MQ-proxy 5577 5578
  ```

- Start the `NexusWriter` service container

  - Create docker image. The necessary Dockerfile is provided.

    ```bash
    docker build --no-cache -t bluesky_nexus_writer:latest .
    ```

  - Start container based on the created image: `bluesky_nexus_writer`

    - Make the script executable

      ```bash
      chmod +x scripts/start_bluesky_nexus_container.sh
      ```

    - Execute the script

      ```bash
      ./ scripts/start_bluesky_nexus_container.sh
      ```

    Note: The host directories defined in `start_bluesky_nexus_container.sh` can be changed according to your needs/system:
    - HOST_DATA_DIR="$HOME/nexus_output" # This is a NeXus file directory used by `NexusWriter`
    - HOST_LOG_DIR="$HOME/nexus_logs" # This is a log file directory used by `NexusWriter`

  The `NexusWriter` service container  starts a python script "scripts/start_bluesky_nexus_writer_dispatcher.py" when the container is launched.

  The script:
  - instantiates a `RemoteDispatcher` listening on port 5578,
  - registers a `NexusWriter` callback inside this separate process,
  - starts the `RemoteDispatcher` so that documents received on port 5578 can be processed by the `NexusWriter`.

In your script:

- Add imports

  ```python
  from bluesky_nexus.preprocessors.supplemental_metadata import SupplementalMetadata
  from bluesky_nexus.common.logging_utils import setup_nx_logger, LogLevel
  ```

- Add optional NeXus logging setup

  ```python
  nx_log_file_dir_path: str = "Your path to the NeXus log file directory"
  setup_nx_logger(
      console_level=LogLevel.ERROR,
      file_level=LogLevel.DEBUG,
      log_file_dir_path=nx_log_file_dir_path,
      log_file_name="nx_log.log",
      log_format=None,  # Uses default format if None
      log_file_max_size=10 * 1024 * 1024,  # 10 MB
      backup_count=5,
      enable_console=True,
      enable_file=True,
  )
  ```

  See the section [Explanations on the optional NeXus logger](#explanations-on-the-optional-nexus-logger)
  for detailed information on the logger configuration.

- Add NeXus metadata to the start document

  ```python
  # Let the preprocessor append NeXus metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.NEXUS_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.NEXUS_MD)
  RE.preprocessors.append(metadata)
  ```

- Add device metadata to the start document

  ```python
  # Let the preprocessor append devices metadata to the start document

  # using keyword arguments (recommended)
  metadata = SupplementalMetadata(devices_dictionary=devices_dictionary, md_type=SupplementalMetadata.MetadataType.DEVICE_MD)
  # or using positional arguments
  metadata = SupplementalMetadata(devices_dictionary, SupplementalMetadata.MetadataType.DEVICE_MD)
  RE.preprocessors.append(metadata)
  ```

- Important: Do not subscribe NexusWriter in your RE script. In this mode, your experiment script must NOT contain:

  ```python
  nexus_writer = NexusWriter(...)
  RE.subscribe(nexus_writer)
  ```

  This completes the remote mode setup.

---

## NeXus directory structure

The `NexusWriter` creates a structured directory tree under the configured `nx_file_dir_path`. The directory structure follows:

```swift
{nx_file_dir_path}/{base_name}/{exp_name}/
```

Where:

- nx_file_dir_path – mandaotry directory path passed to the `NexusWriter`
- base_name – optional metadata key in the plan
- exp_name – optional metadata key in the plan

These values are passed in the plan metadata:

```python
md = {
    "base_name": "UE112",
    "exp_name": "double_slit_exp",
}
```

Notes:

- If `base_name` is not provided → that folder level is omitted
- If `exp_name` is not provided → that folder level is omitted
- If both are omitted → files go directly into {nx_file_dir_path}

Example:

```python
nx_file_dir_path = "/data/nexus"
md = {"base_name": "beamlineA", "exp_name": "test_experiment"}
```

Final directory:

```bash
/data/nexus/beamlineA/test_experiment/
```

## NeXus file naming conventions

The `NexusWriter` determines the file naming based on metadata provided in the Bluesky plan.
Two situations must be distinguished:

1) The user/operator provides a file name via `nx_file_name`
2) The user/operator does not provide a file name (or provides an empty string)

### Case 1 — User provides `nx_file_name`

If the user passes:

```python
md = {"nx_file_name": "my_scan"}
```

or

```python
md = {"nx_file_name": "my_scan.nxs"}
```

Naming behavior:

- The `NexusWriter` uses exactly this name.
- If the file name has no extension, .nxs is automatically appended.
- Each new run overwrites the file if the same name is provided.

Note: No UID, scan ID, or plan name is added.
This mode gives explicit user control over naming and overwriting.

### Case 2 — User does not provide `nx_file_name` (or value is empty)

If

```python
"nx_file_name" not in md
```

or

```python
md = {"nx_file_name": ""}
```

then the NeXus filename is automatically generated based on run metadata.

#### Auto-generated filename format

```css
{scan_id:04d}_{plan_name}_{uid8}.nxs
```

Where:

- scan_id:04d – zero-padded 4-digit integer
  - 3 → 0003
  - 15 → 0015
- plan_name – taken from the start document (start_doc["plan_name"])
- uid8 – first 8 UID chars, dashes removed
- .nxs – extension always appended

#### Example

Metadata:

```python
md = {"base_name": "beamlineA", "exp_name": "overnight"}
```

Run metadata:

- scan_id = 12 → 0012
- plan_name = "scan"
- UID = "c5f9-a1e4-7a53-4a02-8199-efb4cd02bddc" → uid8 = "c5f9a1e4"

Resulting full path:

```bash
/data/nexus/beamlineA/overnight/0012_scan_c5f9a1e4.nxs
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
