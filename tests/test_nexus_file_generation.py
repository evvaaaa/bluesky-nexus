"""Integration tests.

Verification of Bluesky run metadata and NeXus file generation.

This module contains tests designed to validate the creation, structure, and content
of NeXus files produced by executing Bluesky plans with simulated hardware devices.
The tests focus on ensuring that metadata, device states, and plan results are
accurately captured and stored in compliance with the expected NeXus schema.

Key components tested include:
- Configuration and addition of metadata preprocessors to the RunEngine.
- Execution of count plans on simulated devices (e.g., sim_motor).
- Generation and subscription of callbacks for structured metadata logging.
- Verification of NeXus file creation, including group hierarchy, attributes,
  and dataset values with expected data types and shapes.
- Cleanup of generated files post-validation to maintain a clean test environment.

Auxiliary debugging functions are provided to assist in examining NumPy array data
for discrepancies during test failures.

Run this module with pytest to execute all included tests.

Example usage:
    pytest test_module.py
"""

# pylint: disable=too-many-lines
# pylint: disable=line-too-long

import ast

# Activate for Debuging only
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
from types import GeneratorType
from typing import Any, Dict, Union

import bluesky.plan_stubs as bps
import h5py
import numpy as np
import pytest
from bluesky import RunEngine
from bluesky.plans import count, scan
from h5py.h5t import CSET_UTF8
from ophyd.sim import motor  # pylint: disable=no-name-in-module

from bluesky_nexus.bluesky_nexus_const import CALLBACK_FILE_EXTENSION, NX_FILE_EXTENSION
from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.preprocessors.supplemental_metadata import SupplementalMetadata
from bluesky_nexus.utils.callbacks import WriteToFileFormattedCallback
from tests.devices.mock_flyer import MockFlyer
from tests.devices.mono import Mono
from tests.devices.mono_with_grating_cpt import MonoWithGratingCpt
from tests.devices.sim_motor import SimMotor
from tests.preprocessors.baseline import SupplementalDataBaseline

# Constants: Define paths
NX_FILE_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "nx_file"))
CALLBACK_FILE_DIR_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "callback_file")
)

NX_SCHEMA_DIR_PATH = os.path.abspath(
    os.path.join(os.path.join(os.path.dirname(__file__), "devices"), "nx_schema")
)


# Fixture: Ensure the `nx_file` directory exists
@pytest.fixture
def create_nx_file_dir() -> None:
    """Create nx_file_dir.

    Creates the `nx_file` directory if it doesn't already exist and cleans up
    after the tests.
    """
    if not os.path.exists(NX_FILE_DIR_PATH):
        os.makedirs(NX_FILE_DIR_PATH)


# Fixture: Ensure the `callback_file` directory exists
@pytest.fixture
def create_callback_file_dir() -> None:
    """Create callback_file_dir.

    Creates the `callback_file` directory if it doesn't already exist and cleans up
    after the tests.
    """
    if not os.path.exists(CALLBACK_FILE_DIR_PATH):
        os.makedirs(CALLBACK_FILE_DIR_PATH)


# Fixture: Get the path to `nx_file` directory
@pytest.fixture
def _nx_file_dir_path() -> str:
    """Return nx_file dir_path.

    Returns the absolute path to the `nx_file` directory for storing output files.
    """
    return NX_FILE_DIR_PATH


# Fixture: Get the path to `callback_file` directory
@pytest.fixture
def _callback_file_dir_path() -> str:
    """Return callback file_dir_path.

    Returns the absolute path to the `callback_file` directory for storing callback
    files.
    """
    return CALLBACK_FILE_DIR_PATH


# Test: Example test that writes to `nx_file`
@pytest.mark.skip(reason="Temporarily disabling this test_write_to_nx_file_dir")
def test_write_to_nx_file_dir() -> None:
    """Create and write to a file in the NX file directory."""
    test_file_path = os.path.join(NX_FILE_DIR_PATH, "test_output.txt")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("This is a test file.")
    assert os.path.exists(test_file_path)


# Test: Ensure the `nx_schema` directory exists
def test_nx_schema_directory_exists() -> None:
    """Test if nx_schema directory exists.

    Test to ensure that the `nx_schema` directory exists in the same parent directory
    as this test file.
    """
    assert os.path.isdir(
        NX_SCHEMA_DIR_PATH
    ), f"The directory `nx_schema` does not exist at {NX_SCHEMA_DIR_PATH}"


# Fixture: Get the path to `nx_schema`
@pytest.fixture
def _nx_schema_dir_path() -> str:
    """Return nx_schema dir_path.

    Returns the absolute path to the `nx_schema` directory for storing schema files.
    """
    return NX_SCHEMA_DIR_PATH


# Constants for the expected files
EXPECTED_FILES = ["mono.py", "mono_with_grating_cpt.py"]


# Test: Ensure specific files exist in the `nx_schema` directory
def test_expected_files_exist_in_nx_schema(_nx_schema_dir_path) -> None:
    """Test if expected files exist in nx_schema.

    Test to ensure that specific files exist in the `nx_schema` directory.

    Expected files:
    - mono.py
    - mono_with_grating_cpt.py
    """
    missing_files = []
    for file_name in EXPECTED_FILES:
        file_path = os.path.join(_nx_schema_dir_path, file_name)
        if not os.path.isfile(file_path):
            missing_files.append(file_name)

    assert not missing_files, (
        "The following expected files are missing in the `nx_schema` "
        f"directory: {', '.join(missing_files)}"
    )


# Fixture: Create a dictionary of devices for reuse in tests
@pytest.fixture
def _devices_dictionary() -> (
    Dict[str, Union[Mono, MonoWithGratingCpt, SimMotor, MockFlyer]]
):
    """Create and return a dictionary of test devices.

    This includes monochromators with and without grating components.
    """
    mono: Mono = Mono(name="mono")
    mono_with_grating_cpt: MonoWithGratingCpt = MonoWithGratingCpt(
        name="mono_with_grating_cpt"
    )
    sim_motor: SimMotor = SimMotor(name="sim_motor")
    mock_flyer: MockFlyer = MockFlyer(name="mock_flyer", wait_seconds=3)

    return {
        "mono": mono,
        "mono_with_grating_cpt": mono_with_grating_cpt,
        "sim_motor": sim_motor,
        "mock_flyer": mock_flyer,
    }


# Fixture: number of scan steps
@pytest.fixture
def _scan_step_number():
    """Return number of plan's steps."""
    return 10


# Fixture: number of counts
@pytest.fixture
def _counts_number():
    """Return number of counts."""
    return 10


# Fixture: Baseline configuration for test 1
@pytest.fixture
def _baseline_1(_devices_dictionary):
    """Return baseline configuration.

    Participating devices: 'mono' and 'mono_with_grating_cpt'.
    """
    return [_devices_dictionary["mono"], _devices_dictionary["mono_with_grating_cpt"]]


# Fixture: Baseline configuration for test 2
@pytest.fixture
def _baseline_2(_devices_dictionary):
    """Return baseline configuration.

    Participating devices: 'mono'.
    """
    return [_devices_dictionary["mono"]]


# Fixture: Baseline configuration for test 3
@pytest.fixture
def _baseline_3(_devices_dictionary):
    """Return baseline configuration.

    Participating devices: 'mono_with_grating_cpt'.
    """
    return [_devices_dictionary["mono_with_grating_cpt"]]


# Fixture: Baseline configuration for test 4. Empty baseline.
@pytest.fixture
def _baseline_4():
    """Return baseline configuration.

    No participating devices.
    """
    return []


# Fixture: Baseline configuration for test 6
@pytest.fixture
def _baseline_5(_devices_dictionary):
    """Return baseline configuration.

    Participating devices: 'mono_with_grating_cpt'.
    """
    return [_devices_dictionary["mock_flyer"]]


# Fixture: Initialize a plain Bluesky RunEngine
@pytest.fixture
def _run_engine():
    """Initialize and return a plain Bluesky RunEngine.

    No subscriptions are added yet.
    """
    return RunEngine()


# Fixture: Subscribe NexusWriter callback to the RunEngine
@pytest.fixture
def _run_eng(_run_engine: RunEngine, _nx_file_dir_path: str):
    """Subscribe the NexusWriter callback to a given RunEngine.

    Returns the configured RunEngine.
    """
    nexus_writer = NexusWriter(nx_file_dir_path=_nx_file_dir_path)

    _run_engine.subscribe(nexus_writer)
    return _run_engine


# Fixture: Return ophyd sim motor
@pytest.fixture
def _my_motor():
    """Return motor object."""
    return motor  # Return the motor object for use in tests


def execute_fly_plan(_run_eng: RunEngine, md: dict, device: MockFlyer):
    """Define and execute a fly plan on the RunEngine."""

    def mock_fly():
        yield from bps.open_run()
        yield from bps.kickoff(device)
        yield from bps.complete(device, group="group")
        yield from bps.wait(group="group", timeout=10)
        yield from bps.collect(device)
        yield from bps.close_run()

    plan = mock_fly()
    assert isinstance(plan, GeneratorType), "mock_fly() is not returning a generator!"
    _run_eng.md = md
    _run_eng(plan)
    # _run_eng(plan, lambda n, d: print("===========\n", n, pformat(d)))


# Helper: Execute a scan plan on the RunEngine
def execute_scan_plan(
    _run_eng: RunEngine,
    md: dict,
    detectors: list[object],
    _my_motor: object,
    _scan_step_number: int,
):
    """Define and execute a scan plan on the RunEngine.

    Scan detectors over a motor's range with given metadata.
    """

    def scan_plan():
        plan = scan(
            detectors, _my_motor, 1, 10, _scan_step_number, md=md
        )  # Start, stop, steps
        assert isinstance(plan, GeneratorType), "scan() is not returning a generator!"
        yield from plan

    _run_eng(scan_plan())


# Helper: Execute a count plan on the RunEngine
def execute_count_plan(
    _run_eng: RunEngine,
    md: dict,
    detectors: list[object],
    _counts_number: int,
):
    """Define and execute a count plan on the RunEngine.

    - Repeat reading the detectors `num_counts` times with provided metadata.
    """

    def count_plan():
        plan = count(detectors, num=_counts_number, md=md)
        assert isinstance(plan, GeneratorType), "count() is not returning a generator!"
        yield from plan

    _run_eng(count_plan())


# Helper: Add preprocessors to the RunEngine for baseline and metadata
def add_preprocessors(re: RunEngine, devices_dictionary: dict, baseline: list[object]):
    """Add preprocessors to the RunEngine to handle following tasks.

    - Baseline devices.
    - Nexus metadata and device metadata for start documents.
    """
    # Append baseline devices
    sdd = SupplementalDataBaseline(baseline=baseline)
    re.preprocessors.append(sdd)

    # Add Nexus metadata
    metadata = SupplementalMetadata()
    metadata.devices_dictionary = devices_dictionary
    metadata.md_type = SupplementalMetadata.MetadataType.NEXUS_MD
    re.preprocessors.append(metadata)

    # Add device metadata
    metadata = SupplementalMetadata()
    metadata.devices_dictionary = devices_dictionary
    metadata.md_type = SupplementalMetadata.MetadataType.DEVICE_MD
    re.preprocessors.append(metadata)


# Helper: Generate metadata for the start document
def generate_md(nx_file_name: str, title: str, definition: str, test_dict: dict):
    """Generate metadata dict."""
    return {
        "nx_file_name": nx_file_name,  # Facultative
        "title": title,  # Facultative
        "definition": definition,  # Facultative
        "test_dict": test_dict,  # Facultative
    }


# Helper: to get file path to the nexus file
def get_nx_file_path(file_dir_path: str, file_name: str) -> str:
    """Return nexus file path."""
    # Add extension to file name
    if not file_name.endswith(NX_FILE_EXTENSION):
        file_name = file_name + NX_FILE_EXTENSION

    # Define nexus file path
    file_path: str = os.path.join(file_dir_path, file_name)
    return file_path


# Helper: to get file path to the callback file
def get_callback_file_path(file_dir_path: str, file_name: str) -> str:
    """Return callback file path."""
    # Add extension to file name
    if not file_name.endswith(CALLBACK_FILE_EXTENSION):
        file_name = file_name + CALLBACK_FILE_EXTENSION

    # Define file path
    file_path: str = os.path.join(file_dir_path, file_name)
    return file_path


# Helper: Remove a file
def clean_up(file_path: str) -> None:
    """Clean up file."""
    if os.path.exists(file_path):
        os.remove(file_path)
    print(f"Proc info: Clean up of file: {file_path} finished.")


def _assert_attribute_equal(
    attr_key: str, nexus_value: Any, expected_value: Any, item_path: str
) -> None:
    if isinstance(nexus_value, str) and isinstance(expected_value, str):
        assert (
            nexus_value == expected_value
        ), f"Mismatch in string: Expected {expected_value}, Found {nexus_value}"

    elif isinstance(nexus_value, (int, float)) and isinstance(
        expected_value, (int, float)
    ):
        assert np.isclose(
            nexus_value, expected_value
        ), f"Mismatch in float: Expected {expected_value}, Found {nexus_value}"

    elif isinstance(nexus_value, np.ndarray) or isinstance(expected_value, list):
        if isinstance(expected_value, list):
            expected_value = np.array(expected_value)

        if np.issubdtype(nexus_value.dtype, np.number) and np.issubdtype(
            expected_value.dtype, np.number
        ):
            assert np.allclose(
                nexus_value, expected_value
            ), f"Mismatch in array: Expected {expected_value}, Found {nexus_value}"
        else:
            assert np.array_equal(
                nexus_value, expected_value
            ), f"Mismatch in array: Expected {expected_value}, Found {nexus_value}"

    elif (
        isinstance(nexus_value, str)
        and nexus_value.startswith("{")
        and nexus_value.endswith("}")
    ) or isinstance(expected_value, dict):
        try:
            nexus_dict = (
                ast.literal_eval(nexus_value)
                if isinstance(nexus_value, str)
                else nexus_value
            )
            expected_dict = (
                ast.literal_eval(expected_value)
                if isinstance(expected_value, str)
                else expected_value
            )
        except (SyntaxError, ValueError) as err:
            raise ValueError(
                f"Invalid dictionary format for attribute "
                f"'{attr_key}' in group '{item_path}'"
            ) from err

        assert (
            nexus_dict == expected_dict
        ), f"Mismatch in dictionary: Expected {expected_dict}, Found {nexus_dict}"

    else:
        assert (
            nexus_value == expected_value
        ), f"Mismatch in value: Expected {expected_value}, Found {nexus_value}"


def _verify_structure(
    f: h5py.File, expected_structure: Dict[str, Dict[str, Any]]
) -> None:
    for item_path, item_attrs in expected_structure.items():
        keys = item_path.split("/")
        current = f
        for key in keys:
            assert key in current, f"Missing group: {key} in path: {item_path}"
            current = current[key]

        for attr_key, attr_value in item_attrs.items():
            # print("attr_key:", attr_key) # Debug only
            # print("attr_value:", attr_value) # Debug only
            assert (
                attr_key in current.attrs
            ), f"Missing attribute: {attr_key} in group: {item_path}"
            nexus_value = current.attrs[attr_key]
            _assert_attribute_equal(attr_key, nexus_value, attr_value, item_path)


def _verify_dataset(f: h5py.File, dataset_path: str, expected: Any) -> None:
    keys = dataset_path.split("/")
    current = f
    for key in keys:
        assert (
            key in current
        ), f"Missing dataset key: {key} in dataset path: {dataset_path}"
        current = current[key]

    assert isinstance(current, h5py.Dataset), f"{dataset_path} is not a dataset"
    actual_value = current[()]
    assert isinstance(actual_value, np.ndarray), f"{dataset_path} is not a numpy array"

    # print("actual_value.dtype: ", {actual_value.dtype})

    expected_value = expected.get("value") if isinstance(expected, dict) else expected
    expected_dtype = expected.get("dtype") if isinstance(expected, dict) else None
    expected_shape = expected.get("shape") if isinstance(expected, dict) else None

    # Verify dtype
    if expected_dtype:
        assert actual_value.dtype == np.dtype(expected_dtype), (
            f"Mismatch in dtype for dataset: {dataset_path}: "
            f"Expected {expected_dtype}, Found {actual_value.dtype}"
        )

        if actual_value.dtype.kind == "O":
            h5_type = current.id.get_type()
            assert (
                h5_type.get_class()
                == h5py.h5t.STRING  # pylint: disable=c-extension-no-member
            ), f"Dataset {dataset_path} is not a string type"
            assert (
                h5_type.get_cset() == CSET_UTF8
            ), f"Dataset {dataset_path} is not UTF-8 encoded"
            assert (
                h5_type.is_variable_str()
            ), f"Dataset {dataset_path} does not use variable-length UTF-8 strings"

    # Verify shape
    if expected_shape:
        assert actual_value.shape == expected_shape, (
            f"Mismatch in shape for dataset: {dataset_path}: "
            f"Expected {expected_shape}, Found {actual_value.shape}"
        )

    if expected_value is None:
        return

    expected_value = np.array(
        expected_value, dtype=object if actual_value.dtype.kind == "O" else None
    )
    if actual_value.dtype.kind in ("f", "i"):
        assert np.allclose(actual_value, expected_value, atol=1e-8), (
            f"Mismatch in dataset: {dataset_path}: Expected {expected_value}, "
            f"Found {actual_value}"
        )
    else:
        assert np.array_equal(actual_value, expected_value), (
            f"Mismatch in dataset: {dataset_path}: Expected {expected_value}, "
            f"Found {actual_value}"
        )

    # Determine the data type kind of the actual array
    dtype_kind = actual_value.dtype.kind
    # Define the error message
    error_msg = (
        f"Mismatch in dataset: {dataset_path}: Expected {expected_value}, "
        f"Found {actual_value}"
    )

    # Check if the array contains objects/string values
    if "O" == dtype_kind:
        expected_value = np.array(expected_value, dtype=object)
        assert np.array_equal(
            actual_value,
            expected_value,
        ), error_msg

    # Check if the array contains numeric values
    elif dtype_kind in ("f", "i"):  # 'f' for float, 'i' for integer
        expected_value = np.array(expected_value)
        assert np.allclose(
            actual_value,
            expected_value,
            atol=1e-8,  # Use tolerance of 1e-8 (adjust as needed)
        ), error_msg

    # Check if the array contains boolean values
    elif "b" == dtype_kind:
        expected_value = np.array(expected_value)
        assert np.array_equal(
            actual_value,
            expected_value,
        ), error_msg

    else:
        raise ValueError(
            f"Dataset {dataset_path} has a unsupported datatype: " f"{dtype_kind}"
        )


def verify_nexus_file(
    file_path: str, expected_structure: dict, expected_data: dict
) -> None:
    """Verify the NeXus file structure and its data."""
    with h5py.File(file_path, "r") as f:
        _verify_structure(f, expected_structure)
        for dataset_path, expected in expected_data.items():
            _verify_dataset(f, dataset_path, expected)


# Test function
# @unittest.skip("Temporarily disabling this test_1")
def test_1(
    _run_eng,
    _devices_dictionary,
    _baseline_1,
    _my_motor,
    _callback_file_dir_path,
    _nx_file_dir_path,
    _scan_step_number,
    request,
) -> None:
    """Integration test for generating and verifying a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a plan and verifies the resulting Nexus file's structure and data.
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_1)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"
    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 1",
        "NX_abc",
        {"a": 1, "b": 2, "c": {"d": 3, "e": 4}},
    )

    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_scan_plan(
            _run_eng, md, [_devices_dictionary["mono"].en], _my_motor, _scan_step_number
        )

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while executing "
        f"test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes ---
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes---
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mono and its attributes ---
        # ---
        "entry/instrument/mono": {
            "NX_class": "NXmonochromator",
            "nx_model": "NXmonochromatorModel",
            "attr_0": 3.1415,
            "attr_1": {"a": "2"},
            "attr_2": "{'b':'1'}",
            "attr_3": [1.02, 3.04, 5.06],
            "attr_4": [5, 6, 7],
            "attr_5": True,
            "default": "energy",
            "value": "3.1415",
        },
        # ---
        # --- field: entry/instrument/mono/energy and its attributes ---
        # ---
        "entry/instrument/mono/energy": {
            "NX_class": "NX_FLOAT",
            "PI": 3.1415,
            "days": ["Mo", "We"],
            "destination": '{"departement": "A23"}',
            "factors": [1.34, 2.78],
            "object_name": "mono_en",
            "precision": 3,
            "prices": "Euro",
            "shape": [10],
            "source": "SIM:mono_en",
            "transformation": "{'expression': '3 * x**2 + np.exp(np.log(5)) + 1', "
            "'target': 'value'}",
            "units": "keV",
            "value": 12.34,
        },
        # ---
        # --- field: entry/instrument/mono/energy_timestamps and its attributes
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: energy extracted from the "
            "events",
        },
        # ---
        # --- field: entry/instrument/mono/events_timestamps and its attributes
        # ---
        "entry/instrument/mono/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the events",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset and its attributes
        # ---
        "entry/instrument/mono/someDataset": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "precision": 3,
            "object_name": "mono_en",
            "source": "SIM:mono_en",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset_timestamps and its attributes
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: someDataset extracted from "
            "the events",
        },
        # ---
        # --- group: entry/instrument/mono/GRATING and its attributes
        # ---
        "entry/instrument/mono/GRATING": {
            "NX_class": "NXgrating",
            "attr_0": "new",
            "default": "diffraction_order",
            "value": 167,
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order
        # --- and its attributes
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "NX_class": "NX_INT",
            "at_0": 13.14,
            "at_1": [2.03, 4.05],
            "value": "some_value",
        },
        # ---
        # --- group: entry/instrument/mono/TRANSFORMATIONS and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS": {
            "NX_class": "NXtransformations",
            "attr_0": 3.1415,
            "attr_1": '{"a": "2"}',
            "attr_2": [1.01, 2.02],
            "default": "alpha",
            "value": "3.1",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "NX_class": "NX_CHAR",
            "depends_on": "x",
            "equipment_component": "A.71",
            "offset": 34.56,
            "offset_units": "um",
            "units": "um",
            "value": 123,
            "vector": [0, 1, 0],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # --- and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "NX_class": "NX_FLOAT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps and
        # --- its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_end extracted from "
            "the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # --- and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "NX_class": "NX_INT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # --- timestamps and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_increment_set extracted "
            "from the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps
        # --- and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/instrument/mono/someGroup and its attributes
        # ---
        "entry/instrument/mono/someGroup": {
            "NX_class": "NXsomeClass",
            "attr_1": '{"a": "2"}',
            "attr_2": [5.06, 7.08],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy and its attributes
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "NX_class": "NX_FLOAT",
            "attr_1": "PI",
            "attr_2": 3.1415,
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: energy extracted from the "
            "events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/instrument/mono_with_grating_cpt and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt": {
            "NX_class": "NXmonochromator",
            "default": "energy",
            "nx_model": "NXmonochromatorModel",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy/ and
        # --- its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/energy": {
            "NX_class": "NX_FLOAT",
            "currency": "Euro",
            "object_name": "mono_with_grating_cpt",
            "precision": 3,
            "shape": [2],
            "source": "SIM:mono_with_grating_cpt_engry",
            "units": "keV",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy_timestamps
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: energy extracted from "
            "the events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/events_timestamps
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [2],
        },
        # ---
        # --- group: entry/instrument/mono_with_grating_cpt/GRATING and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING": {
            "NX_class": "NXgrating",
            "default": "diffraction_order",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/
        # --- diffraction_order and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order": {
            "NX_class": "NX_INT",
            "object_name": "mono_with_grating_cpt",
            "shape": [2],
            "source": "SIM:mono_with_grating_cpt_grating_diffraction_order",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/
        # --- diffraction_order_timestamps and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: diffraction_order extracted "
            "from the events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # --- and its attributes ---
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/substrate_material
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/substrate_material": {
            "NX_class": "NX_CHAR",
        },
        # ---
        # --- group: entry/run_info
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/mono": {},
        "entry/run_info/start/device_md/mono_with_grating_cpt": {},
        "entry/run_info/start/hints": {},
        "entry/run_info/start/plan_args": {},
        "entry/run_info/start/plan_pattern_args": {},
        "entry/run_info/start/test_dict": {},
        "entry/run_info/start/versions": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        "entry/instrument/mono/energy": {
            "value": [6.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/energy_timestamps
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/events_timestamps
        # ---
        "entry/instrument/mono/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset
        # ---
        "entry/instrument/mono/someDataset": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset_timestamps
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "value": 0,
            "dtype": "int32",
            "shape": (),  # Scalar
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "value": [b"x"],
            "shape": (1,),  # Scalar
            "dtype": "O",  # Object
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "value": [0.0] * _scan_step_number,
            "dtype": "int32",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # --- timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy ---
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/description
        # ---
        "entry/instrument/mono_with_grating_cpt/description": {
            "value": [b"I am the best mono with grating cpt at the bessyii facility"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy
        # ---
        "entry/instrument/mono_with_grating_cpt/energy": {
            "value": [0.0] * 2,
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/energy_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/events_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order": {
            "value": [0.0] * 2,
            "dtype": "int32",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order
        # --- timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/substrate_material": {
            "value": [b"leadless"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- entry/run_info/start ---
        # ---
        "entry/run_info/start/definition": [b"NX_abc"],
        "entry/run_info/start/detectors": [b"mono_en"],
        "entry/run_info/start/device_md/mono/baseline": [b"True"],
        "entry/run_info/start/device_md/mono/grating_substrate_material": [b"lead"],
        "entry/run_info/start/device_md/mono/worldPosition/x": [b"1.2000000000000003"],
        "entry/run_info/start/device_md/mono/worldPosition/y": [b"4.5000000000000006"],
        "entry/run_info/start/device_md/mono/worldPosition/z": [b"7.8000000000000009"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/baseline": [b"True"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/"
        "grating_substrate_material": [b"leadless"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/x": [
            b"11.120000013"
        ],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/y": [
            b"14.150000016"
        ],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/z": [
            b"17.180000019"
        ],
        "entry/run_info/start/hints/dimensions": [b"[(['motor'], 'primary')]"],
        "entry/run_info/start/motors": [b"motor"],
        "entry/run_info/start/num_intervals": _scan_step_number - 1,
        "entry/run_info/start/num_points": _scan_step_number,
        "entry/run_info/start/nx_file_name": [
            nx_file_name.encode()
        ],  # Encode to obtain byte string since byte string is a value returned from
        # nexus file
        "entry/run_info/start/plan_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_args/detectors": [
            b"SynAxis(prefix='', name='mono_en', parent='mono', "
            b"read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])"
        ],
        "entry/run_info/start/plan_args/num": _scan_step_number,
        "entry/run_info/start/plan_args/per_step": [b"None"],
        "entry/run_info/start/plan_name": [b"scan"],
        "entry/run_info/start/plan_pattern": [b"inner_product"],
        "entry/run_info/start/plan_pattern_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_pattern_args/num": _scan_step_number,
        "entry/run_info/start/plan_pattern_module": [b"bluesky.plan_patterns"],
        "entry/run_info/start/plan_type": [b"generator"],
        "entry/run_info/start/scan_id": 1,
        "entry/run_info/start/test_dict/a": 1,
        "entry/run_info/start/test_dict/b": 2,
        "entry/run_info/start/test_dict/c/d": 3,
        "entry/run_info/start/test_dict/c/e": 4,
        "entry/run_info/start/title": [b"bluesky run test 1"],
        # ---
        # --- entry/run_info/stop ---
        # ---
        "entry/run_info/stop/exit_status": [b"success"],
        "entry/run_info/stop/num_events/baseline": [2],
        "entry/run_info/stop/num_events/primary": _scan_step_number,
        "entry/run_info/stop/reason": [b""],
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)
    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


# Test function
# @unittest.skip("Temporarily disabling this test_2")
def test_2(
    _run_eng,
    _devices_dictionary,
    _baseline_2,
    _my_motor,
    _callback_file_dir_path,
    _nx_file_dir_path,
    _scan_step_number,
    request,
) -> None:
    """Integration test for generating and validating a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a plan and verifies the resulting Nexus file's structure and data.
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_2)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"
    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 2",
        "NX_def",
        {"a": 11, "b": 12, "c": {"d": 13, "e": 14}},
    )

    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_scan_plan(
            _run_eng, md, [_devices_dictionary["mono"].en], _my_motor, _scan_step_number
        )

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while "
        f"executing test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes ---
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes---
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mono and its attributes ---
        # ---
        "entry/instrument/mono": {
            "NX_class": "NXmonochromator",
            "nx_model": "NXmonochromatorModel",
            "attr_0": 3.1415,
            "attr_1": {"a": "2"},
            "attr_2": "{'b':'1'}",
            "attr_3": [1.02, 3.04, 5.06],
            "attr_4": [5, 6, 7],
            "attr_5": True,
            "default": "energy",
            "value": "3.1415",
        },
        # ---
        # --- field: entry/instrument/mono/energy and its attributes
        # ---
        "entry/instrument/mono/energy": {
            "NX_class": "NX_FLOAT",
            "PI": 3.1415,
            "days": ["Mo", "We"],
            "destination": '{"departement": "A23"}',
            "factors": [1.34, 2.78],
            "object_name": "mono_en",
            "precision": 3,
            "prices": "Euro",
            "shape": [10],
            "source": "SIM:mono_en",
            "transformation": "{'expression': '3 * x**2 + np.exp(np.log(5)) + 1', "
            "'target': 'value'}",
            "units": "keV",
            "value": 12.34,
        },
        # ---
        # --- field: entry/instrument/mono/energy_timestamps and its attributes
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: energy extracted from the "
            "events",
        },
        # ---
        # --- field: entry/instrument/mono/events_timestamps and its attributes
        # ---
        "entry/instrument/mono/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the events",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset and its attributes
        # ---
        "entry/instrument/mono/someDataset": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "precision": 3,
            "object_name": "mono_en",
            "source": "SIM:mono_en",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset_timestamps and its attributes
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: someDataset extracted from "
            "the events",
        },
        # ---
        # --- group: entry/instrument/mono/GRATING and its attributes
        # ---
        "entry/instrument/mono/GRATING": {
            "NX_class": "NXgrating",
            "attr_0": "new",
            "default": "diffraction_order",
            "value": 167,
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order
        # --- and its attributes
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "NX_class": "NX_INT",
            "at_0": 13.14,
            "at_1": [2.03, 4.05],
            "value": "some_value",
        },
        # ---
        # --- group: entry/instrument/mono/TRANSFORMATIONS and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS": {
            "NX_class": "NXtransformations",
            "attr_0": 3.1415,
            "attr_1": '{"a": "2"}',
            "attr_2": [1.01, 2.02],
            "default": "alpha",
            "value": "3.1",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "NX_class": "NX_CHAR",
            "depends_on": "x",
            "equipment_component": "A.71",
            "offset": 34.56,
            "offset_units": "um",
            "units": "um",
            "value": 123,
            "vector": [0, 1, 0],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # --- and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "NX_class": "NX_FLOAT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps and
        # --- its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_end extracted from the "
            "events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set and
        # --- its attributes ---
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "NX_class": "NX_INT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # --- timestamps and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_increment_set extracted "
            "from the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/instrument/mono/someGroup and its attributes
        # ---
        "entry/instrument/mono/someGroup": {
            "NX_class": "NXsomeClass",
            "attr_1": '{"a": "2"}',
            "attr_2": [5.06, 7.08],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy and its attributes
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "NX_class": "NX_FLOAT",
            "attr_1": "PI",
            "attr_2": 3.1415,
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: energy extracted from the "
            "events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/run_info ---
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start ---
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/mono": {},
        "entry/run_info/start/hints": {},
        "entry/run_info/start/plan_args": {},
        "entry/run_info/start/plan_pattern_args": {},
        "entry/run_info/start/test_dict": {},
        "entry/run_info/start/versions": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        # ---
        # --- dataset: entry/instrument/mono/energy
        # ---
        "entry/instrument/mono/energy": {
            "value": [6.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/energy_timestamps
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/events_timestamps
        # ---
        "entry/instrument/mono/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset ---
        # ---
        "entry/instrument/mono/someDataset": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset_timestamps
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "value": 0,
            "dtype": "int32",
            "shape": (),  # Scalar
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "value": [b"x"],
            "shape": (1,),  # Scalar
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "value": [0.0] * _scan_step_number,
            "dtype": "int32",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # --- timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- entry/run_info/start ---
        # ---
        "entry/run_info/start/definition": [b"NX_def"],
        "entry/run_info/start/detectors": [b"mono_en"],
        "entry/run_info/start/device_md/mono/baseline": [b"True"],
        "entry/run_info/start/device_md/mono/grating_substrate_material": [b"lead"],
        "entry/run_info/start/device_md/mono/worldPosition/x": [b"1.2000000000000003"],
        "entry/run_info/start/device_md/mono/worldPosition/y": [b"4.5000000000000006"],
        "entry/run_info/start/device_md/mono/worldPosition/z": [b"7.8000000000000009"],
        "entry/run_info/start/hints/dimensions": [b"[(['motor'], 'primary')]"],
        "entry/run_info/start/motors": [b"motor"],
        "entry/run_info/start/num_intervals": _scan_step_number - 1,
        "entry/run_info/start/num_points": _scan_step_number,
        "entry/run_info/start/nx_file_name": [
            nx_file_name.encode()
        ],  # Encode to obtain byte string since byte string is a value returned from
        # nexus file
        "entry/run_info/start/plan_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_args/detectors": [
            b"SynAxis(prefix='', name='mono_en', parent='mono', "
            b"read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])"
        ],
        "entry/run_info/start/plan_args/num": _scan_step_number,
        "entry/run_info/start/plan_args/per_step": [b"None"],
        "entry/run_info/start/plan_name": [b"scan"],
        "entry/run_info/start/plan_pattern": [b"inner_product"],
        "entry/run_info/start/plan_pattern_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_pattern_args/num": _scan_step_number,
        "entry/run_info/start/plan_pattern_module": [b"bluesky.plan_patterns"],
        "entry/run_info/start/plan_type": [b"generator"],
        "entry/run_info/start/scan_id": 1,
        "entry/run_info/start/test_dict/a": 11,
        "entry/run_info/start/test_dict/b": 12,
        "entry/run_info/start/test_dict/c/d": 13,
        "entry/run_info/start/test_dict/c/e": 14,
        "entry/run_info/start/title": [b"bluesky run test 2"],
        # ---
        # --- entry/run_info/stop ---
        # ---
        "entry/run_info/stop/exit_status": [b"success"],
        "entry/run_info/stop/num_events/baseline": 2,
        "entry/run_info/stop/num_events/primary": _scan_step_number,
        "entry/run_info/stop/reason": [b""],
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)
    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


# Test function
# @unittest.skip("Temporarily disabling this test_3")
def test_3(
    _run_eng,
    _devices_dictionary,
    _baseline_3,
    _my_motor,
    _callback_file_dir_path,
    _nx_file_dir_path,
    _scan_step_number,
    request,
) -> None:
    """Integration test for generating and validating a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a plan and verifies the resulting Nexus file's structure and data.
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_3)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"
    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 3",
        "NX_ghi",
        {"a": 21, "b": 22, "c": {"d": 23, "e": 24}},
    )

    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_scan_plan(
            _run_eng, md, [_devices_dictionary["mono"].en], _my_motor, _scan_step_number
        )

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while "
        f"executing test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mono_with_grating_cpt and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt": {
            "NX_class": "NXmonochromator",
            "default": "energy",
            "nx_model": "NXmonochromatorModel",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy/ and its
        # --- attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/energy": {
            "NX_class": "NX_FLOAT",
            "currency": "Euro",
            "object_name": "mono_with_grating_cpt",
            "precision": 3,
            "shape": [2],
            "source": "SIM:mono_with_grating_cpt_engry",
            "units": "keV",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy_timestamps and
        # --- its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: energy extracted from the "
            "events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/events_timestamps and
        # --- its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [2],
        },
        # ---
        # --- group: entry/instrument/mono_with_grating_cpt/GRATING and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING": {
            "NX_class": "NXgrating",
            "default": "diffraction_order",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order": {
            "NX_class": "NX_INT",
            "object_name": "mono_with_grating_cpt",
            "shape": [2],
            "source": "SIM:mono_with_grating_cpt_grating_diffraction_order",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order
        # --- timestamps and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: diffraction_order extracted "
            "from the events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [2],
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/substrate_material
        # --- and its attributes
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/substrate_material": {
            "NX_class": "NX_CHAR",
        },
        # ---
        # --- group: entry/run_info ---
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start ---
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/mono_with_grating_cpt": {},
        "entry/run_info/start/hints": {},
        "entry/run_info/start/plan_args": {},
        "entry/run_info/start/plan_pattern_args": {},
        "entry/run_info/start/test_dict": {},
        "entry/run_info/start/versions": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/description ---
        # ---
        "entry/instrument/mono_with_grating_cpt/description": {
            "value": [b"I am the best mono with grating cpt at the bessyii facility"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy
        # ---
        "entry/instrument/mono_with_grating_cpt/energy": {
            "value": [0.0] * 2,
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/energy_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/energy_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/events_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order": {
            "value": [0.0] * 2,
            "dtype": "int32",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order_
        # --- timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/diffraction_order_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps": {
            "dtype": "float64",
            "shape": (2,),
        },
        # ---
        # --- dataset: entry/instrument/mono_with_grating_cpt/GRATING/events_timestamps
        # ---
        "entry/instrument/mono_with_grating_cpt/GRATING/substrate_material": {
            "value": [b"leadless"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- entry/run_info/start ---
        # ---
        "entry/run_info/start/definition": [b"NX_ghi"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/baseline": [b"True"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/"
        "grating_substrate_material": [b"leadless"],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/x": [
            b"11.120000013"
        ],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/y": [
            b"14.150000016"
        ],
        "entry/run_info/start/device_md/mono_with_grating_cpt/worldPosition/z": [
            b"17.180000019"
        ],
        "entry/run_info/start/hints/dimensions": [b"[(['motor'], 'primary')]"],
        "entry/run_info/start/motors": [b"motor"],
        "entry/run_info/start/num_intervals": _scan_step_number - 1,
        "entry/run_info/start/num_points": _scan_step_number,
        "entry/run_info/start/nx_file_name": [
            nx_file_name.encode()
        ],  # Encode to obtain byte string since byte string is a value returned from
        # nexus file
        "entry/run_info/start/plan_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_args/detectors": [
            b"SynAxis(prefix='', name='mono_en', parent='mono', "
            b"read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])"
        ],
        "entry/run_info/start/plan_args/num": _scan_step_number,
        "entry/run_info/start/plan_args/per_step": [b"None"],
        "entry/run_info/start/plan_name": [b"scan"],
        "entry/run_info/start/plan_pattern": [b"inner_product"],
        "entry/run_info/start/plan_pattern_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_pattern_args/num": _scan_step_number,
        "entry/run_info/start/plan_pattern_module": [b"bluesky.plan_patterns"],
        "entry/run_info/start/plan_type": [b"generator"],
        "entry/run_info/start/scan_id": 1,
        "entry/run_info/start/test_dict/a": 21,
        "entry/run_info/start/test_dict/b": 22,
        "entry/run_info/start/test_dict/c/d": 23,
        "entry/run_info/start/test_dict/c/e": 24,
        "entry/run_info/start/title": [b"bluesky run test 3"],
        # ---
        # --- entry/run_info/stop ---
        # ---
        "entry/run_info/stop/exit_status": [b"success"],
        "entry/run_info/stop/num_events/baseline": 2,
        "entry/run_info/stop/num_events/primary": _scan_step_number,
        "entry/run_info/stop/reason": [b""],
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)
    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


# Test function
# @unittest.skip("Temporarily disabling this test_4")
def test_4(
    _run_eng,
    _devices_dictionary,
    _baseline_4,
    _my_motor,
    _callback_file_dir_path,
    _nx_file_dir_path,
    _scan_step_number,
    request,
) -> None:
    """Integration test for generating and validating a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a plan and verfifies the resulting Nexus file's structure and data.
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_4)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"
    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 4",
        "NX_jkl",
        {"a": 31, "b": 32, "c": {"d": 33, "e": 34}},
    )

    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_scan_plan(
            _run_eng, md, [_devices_dictionary["mono"].en], _my_motor, _scan_step_number
        )

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while "
        f"executing test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes ---
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes---
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mono and its attributes ---
        # ---
        "entry/instrument/mono": {
            "NX_class": "NXmonochromator",
            "nx_model": "NXmonochromatorModel",
            "attr_0": 3.1415,
            "attr_1": {"a": "2"},
            "attr_2": "{'b':'1'}",
            "attr_3": [1.02, 3.04, 5.06],
            "attr_4": [5, 6, 7],
            "attr_5": True,
            "default": "energy",
            "value": "3.1415",
        },
        # ---
        # --- field: entry/instrument/mono/energy and its attributes
        # ---
        "entry/instrument/mono/energy": {
            "NX_class": "NX_FLOAT",
            "PI": 3.1415,
            "days": ["Mo", "We"],
            "destination": '{"departement": "A23"}',
            "factors": [1.34, 2.78],
            "object_name": "mono_en",
            "precision": 3,
            "prices": "Euro",
            "shape": [10],
            "source": "SIM:mono_en",
            "transformation": "{'expression': '3 * x**2 + np.exp(np.log(5)) + 1', "
            "'target': 'value'}",
            "units": "keV",
            "value": 12.34,
        },
        # ---
        # --- field: entry/instrument/mono/energy_timestamps and its attributes
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: energy extracted from the "
            "events",
        },
        # ---
        # --- field: entry/instrument/mono/events_timestamps and its attributes
        # ---
        "entry/instrument/mono/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the events",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset and its attributes
        # ---
        "entry/instrument/mono/someDataset": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "precision": 3,
            "object_name": "mono_en",
            "source": "SIM:mono_en",
        },
        # ---
        # --- field: entry/instrument/mono/someDataset_timestamps and its attributes
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "NX_class": "NX_FLOAT",
            "shape": [10],
            "description": "Timestamps of the component: someDataset extracted from "
            "the events",
        },
        # ---
        # --- group: entry/instrument/mono/GRATING and its attributes ---
        # ---
        "entry/instrument/mono/GRATING": {
            "NX_class": "NXgrating",
            "attr_0": "new",
            "default": "diffraction_order",
            "value": 167,
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order and its
        # --- attributes
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "NX_class": "NX_INT",
            "at_0": 13.14,
            "at_1": [2.03, 4.05],
            "value": "some_value",
        },
        # ---
        # --- group: entry/instrument/mono/TRANSFORMATIONS and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS": {
            "NX_class": "NXtransformations",
            "attr_0": 3.1415,
            "attr_1": '{"a": "2"}',
            "attr_2": [1.01, 2.02],
            "default": "alpha",
            "value": "3.1",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "NX_class": "NX_CHAR",
            "depends_on": "x",
            "equipment_component": "A.71",
            "offset": 34.56,
            "offset_units": "um",
            "units": "um",
            "value": 123,
            "vector": [0, 1, 0],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end and its
        # --- attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "NX_class": "NX_FLOAT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps and
        # --- its attributes ---
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_end extracted from "
            "the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set and
        # --- its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "NX_class": "NX_INT",
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_
        # --- timestamps and its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: alpha_increment_"
            "set extracted from the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps and
        # --- its attributes
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/instrument/mono/someGroup and its attributes
        # ---
        "entry/instrument/mono/someGroup": {
            "NX_class": "NXsomeClass",
            "attr_1": '{"a": "2"}',
            "attr_2": [5.06, 7.08],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy and its attributes
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "NX_class": "NX_FLOAT",
            "attr_1": "PI",
            "attr_2": 3.1415,
            "object_name": "mono_en",
            "precision": 3,
            "shape": [10],
            "source": "SIM:mono_en",
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the component: energy extracted "
            "from the events",
            "shape": [10],
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps and its
        # --- attributes
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "NX_class": "NX_FLOAT",
            "description": "Timestamps of the events",
            "shape": [10],
        },
        # ---
        # --- group: entry/run_info ---
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start ---
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/mono": {},
        "entry/run_info/start/hints": {},
        "entry/run_info/start/plan_args": {},
        "entry/run_info/start/plan_pattern_args": {},
        "entry/run_info/start/test_dict": {},
        "entry/run_info/start/versions": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        # ---
        # --- dataset: entry/instrument/mono/energy
        # ---
        "entry/instrument/mono/energy": {
            "value": [6.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/energy_timestamps
        # ---
        "entry/instrument/mono/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/events_timestamps
        # ---
        "entry/instrument/mono/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset
        # ---
        "entry/instrument/mono/someDataset": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someDataset_timestamps
        # ---
        "entry/instrument/mono/someDataset_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/GRATING/diffraction_order
        # ---
        "entry/instrument/mono/GRATING/diffraction_order": {
            "value": 0,
            "dtype": "int32",
            "shape": (),  # Scalar
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha": {
            "value": [b"x"],
            "shape": (1,),  # Scalar
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_end
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_end_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set": {
            "value": [0.0] * _scan_step_number,
            "dtype": "int32",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/
        # --- alpha_increment_set_timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/alpha_increment_set_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/TRANSFORMATIONS/events_timestamps
        # ---
        "entry/instrument/mono/TRANSFORMATIONS/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy
        # ---
        "entry/instrument/mono/someGroup/energy": {
            "value": [0.0] * _scan_step_number,
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/energy_timestamps
        # ---
        "entry/instrument/mono/someGroup/energy_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- dataset: entry/instrument/mono/someGroup/events_timestamps
        # ---
        "entry/instrument/mono/someGroup/events_timestamps": {
            "dtype": "float64",
            "shape": (_scan_step_number,),
        },
        # ---
        # --- entry/run_info/start ---
        # ---
        "entry/run_info/start/definition": [b"NX_jkl"],
        "entry/run_info/start/detectors": [b"mono_en"],
        "entry/run_info/start/device_md/mono/baseline": [b"True"],
        "entry/run_info/start/device_md/mono/grating_substrate_material": [b"lead"],
        "entry/run_info/start/device_md/mono/worldPosition/x": [b"1.2000000000000003"],
        "entry/run_info/start/device_md/mono/worldPosition/y": [b"4.5000000000000006"],
        "entry/run_info/start/device_md/mono/worldPosition/z": [b"7.8000000000000009"],
        "entry/run_info/start/hints/dimensions": [b"[(['motor'], 'primary')]"],
        "entry/run_info/start/motors": [b"motor"],
        "entry/run_info/start/num_intervals": _scan_step_number - 1,
        "entry/run_info/start/num_points": _scan_step_number,
        "entry/run_info/start/nx_file_name": [
            nx_file_name.encode()
        ],  # Encode to obtain byte string since byte string is a value returned from
        # nexus file
        "entry/run_info/start/plan_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_args/detectors": [
            b"SynAxis(prefix='', name='mono_en', parent='mono', "
            b"read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])"
        ],
        "entry/run_info/start/plan_args/num": _scan_step_number,
        "entry/run_info/start/plan_args/per_step": [b"None"],
        "entry/run_info/start/plan_name": [b"scan"],
        "entry/run_info/start/plan_pattern": [b"inner_product"],
        "entry/run_info/start/plan_pattern_args/args": [
            b"SynAxis(prefix='', name='motor', read_attrs=['readback', 'setpoint'], "
            b"configuration_attrs=['velocity', 'acceleration'])",
            b"1",
            b"10",
        ],
        "entry/run_info/start/plan_pattern_args/num": _scan_step_number,
        "entry/run_info/start/plan_pattern_module": [b"bluesky.plan_patterns"],
        "entry/run_info/start/plan_type": [b"generator"],
        "entry/run_info/start/scan_id": 1,
        "entry/run_info/start/test_dict/a": 31,
        "entry/run_info/start/test_dict/b": 32,
        "entry/run_info/start/test_dict/c/d": 33,
        "entry/run_info/start/test_dict/c/e": 34,
        "entry/run_info/start/title": [b"bluesky run test 4"],
        # ---
        # --- entry/run_info/stop ---
        # ---
        "entry/run_info/stop/exit_status": [b"success"],
        "entry/run_info/stop/num_events/primary": _scan_step_number,
        "entry/run_info/stop/reason": [b""],
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)
    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


# Test function
# @unittest.skip("Temporarily disabling this test_5")
def test_5(
    _run_eng,
    _devices_dictionary,
    _baseline_4,
    _callback_file_dir_path,
    _nx_file_dir_path,
    _counts_number,
    request,
) -> None:
    """Integration test for generating and validating a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a count plan for a simulated ophyd motor.readback and verfifies the
        resulting Nexus file's structure and data.
    - sim_motor has deliberately no nx_schema assigned by means of decorator to its
        class definition
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_4)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"
    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 5",
        "NX_mno",
        {"a": 35, "b": 36, "c": {"d": 37, "e": 38}},
    )

    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_count_plan(
            _run_eng, md, [_devices_dictionary["sim_motor"].readback], _counts_number
        )

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while "
        f"executing test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mono and its attributes
        # ---
        "entry/instrument/sim_motor": {
            "NX_class": "NXsimmotor",
            "nx_model": "NXgeneralModel",
        },
        # ---
        # --- group: entry/run_info ---
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start ---
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/sim_motor": {},
        "entry/run_info/start/hints": {},
        "entry/run_info/start/plan_args": {},
        "entry/run_info/start/test_dict": {},
        "entry/run_info/start/versions": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        # ---
        # --- entry/run_info/start
        # ---
        "entry/run_info/start/detectors": [b"sim_motor"],
        "entry/run_info/start/device_md/sim_motor/baseline": [True],
        "entry/run_info/start/device_md/sim_motor/worldPosition/x": [
            b"1.2000000000000003"
        ],
        "entry/run_info/start/device_md/sim_motor/worldPosition/y": [
            b"4.5000000000000006"
        ],
        "entry/run_info/start/device_md/sim_motor/worldPosition/z": [
            b"7.8000000000000009"
        ],
        "entry/run_info/start/hints/dimensions": [b"[(('time',), 'primary')]"],
        "entry/run_info/start/num_intervals": _counts_number - 1,
        "entry/run_info/start/num_points": _counts_number,
        "entry/run_info/start/nx_file_name": [
            nx_file_name.encode()
        ],  # Encode to obtain byte string since byte string is a value returned
        #  from nexus file
        "entry/run_info/start/plan_args/num": _counts_number,
        "entry/run_info/start/plan_name": [b"count"],
        "entry/run_info/start/plan_type": [b"generator"],
        "entry/run_info/start/scan_id": 1,
        "entry/run_info/start/test_dict/a": 35,
        "entry/run_info/start/test_dict/b": 36,
        "entry/run_info/start/test_dict/c/d": 37,
        "entry/run_info/start/test_dict/c/e": 38,
        "entry/run_info/start/title": [b"bluesky run test 5"],
        # ---
        # --- entry/run_info/stop ---
        # ---
        "entry/run_info/stop/exit_status": [b"success"],
        "entry/run_info/stop/num_events/primary": _counts_number,
        "entry/run_info/stop/reason": [b""],
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)
    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


# Test function
# @unittest.skip("Temporarily disabling this test_6")
def test_6(
    _run_eng,
    _devices_dictionary,
    _baseline_5,
    _callback_file_dir_path,
    _nx_file_dir_path,
    request,
) -> None:
    """Integration test for generating and verifying a Nexus file.

    - Configures metadata and baseline devices.
    - Executes a plan and verifies the resulting Nexus file's structure and data.
    """
    # Add preprocessors to the RunEngine
    add_preprocessors(_run_eng, _devices_dictionary, _baseline_5)

    # Generate metadata
    nx_file_name: str = f"hzb_nexus_file_{request.node.name}"

    md: dict = generate_md(
        nx_file_name,
        "bluesky run test 6",
        "NX_fly",
        {"a": 35, "b": 36, "c": {"d": 37, "e": 38}},
    )
    callback_file_path = get_callback_file_path(
        _callback_file_dir_path, f"callback_file_{request.node.name}.json"
    )

    # Execute plan and write generated documents to a json file
    # using 'WriteToFileFormattedCallback'
    with WriteToFileFormattedCallback(callback_file_path) as callback_writer:
        _run_eng.subscribe(callback_writer)
        execute_fly_plan(_run_eng, md, _devices_dictionary["mock_flyer"])

    # Define Nexus file path
    nx_file_path: str = get_nx_file_path(_nx_file_dir_path, nx_file_name)

    # Assert file creation
    assert os.path.exists(nx_file_path), (
        f"Nexus file: {nx_file_path} was not created while executing "
        f"test: {request.node.name}."
    )

    ###
    ### Verify existence of the groups/fields and their attributes
    ###
    expected_structure: dict = {
        # ---
        # --- group: entry and its attributes ---
        # ---
        "entry": {
            "NX_class": "NXentry",
            "Application name": "bluesky_nexus",
            "Content": "'NXinstrument' group and 'NXcollection' group",
        },
        # ---
        # --- group: entry/instrument and its attributes---
        # ---
        "entry/instrument": {
            "NX_class": "NXinstrument",
            "description": "Instruments involved in the bluesky plan",
        },
        # ---
        # --- group: entry/instrument/mock_flyer and its attributes ---
        # ---
        "entry/instrument/mock_flyer": {
            "NX_class": "NXmockflyer",
            "nx_model": "NXgeneralModel",
        },
        # ---
        # --- group: entry/run_info and its attributes---
        # ---
        "entry/run_info": {
            "NX_class": "NXcollection",
            "description": "Copy of the start and stop document from the bluesky run",
        },
        # ---
        # --- groups of: entry/run_info/start ---
        # ---
        "entry/run_info/start": {},
        "entry/run_info/start/device_md/mock_flyer": {},
        "entry/run_info/start/test_dict": {},
        # ---
        # --- groups of: entry/run_info/stop ---
        # ---
        "entry/run_info/stop": {},
        "entry/run_info/stop/num_events": {},
    }

    ###
    ### Verify expected data in datasets. I.e. verify: value, dtype, shape
    ###
    expected_data: dict = {
        # ---
        # --- dataset: entry/run_info/start/device_md/mock_flyer/description ---
        # ---
        "entry/run_info/start/device_md/mock_flyer/description": {
            "value": [b"I am the best flyer"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/definition ---
        # ---
        "entry/run_info/start/definition": {
            "value": [b"NX_fly"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/nx_file_name ---
        # ---
        "entry/run_info/start/nx_file_name": {
            "value": [b"hzb_nexus_file_test_6"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/plan_name ---
        # ---
        "entry/run_info/start/plan_name": {
            "value": [b"mock_fly"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/plan_type ---
        # ---
        "entry/run_info/start/plan_type": {
            "value": [b"generator"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/scan_id ---
        # ---
        "entry/run_info/start/scan_id": {
            "value": 1,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/start/test_dict/a ---
        # ---
        "entry/run_info/start/test_dict/a": {
            "value": 35,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/start/test_dict/b ---
        # ---
        "entry/run_info/start/test_dict/b": {
            "value": 36,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/start/test_dict/c/d ---
        # ---
        "entry/run_info/start/test_dict/c/d": {
            "value": 37,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/start/test_dict/c/e ---
        # ---
        "entry/run_info/start/test_dict/c/e": {
            "value": 38,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/start/time ---
        # ---
        "entry/run_info/start/time": {
            "shape": (1,),
            "dtype": "float64",
        },
        # ---
        # --- dataset: entry/run_info/start/title ---
        # ---
        "entry/run_info/start/title": {
            "value": [b"bluesky run test 6"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/start/uid ---
        # ---
        "entry/run_info/start/uid": {
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/stop/exit_status ---
        # ---
        "entry/run_info/stop/exit_status": {
            "value": [b"success"],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/stop/num_events/baseline ---
        # ---
        "entry/run_info/stop/num_events/baseline": {
            "value": 3,
            "shape": (1,),
            "dtype": "int64",
        },
        # ---
        # --- dataset: entry/run_info/stop/reason ---
        # ---
        "entry/run_info/stop/reason": {
            "value": [b""],
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/stop/run_start ---
        # ---
        "entry/run_info/stop/run_start": {
            "shape": (1,),
            "dtype": "O",
        },
        # ---
        # --- dataset: entry/run_info/stop/time ---
        # ---
        "entry/run_info/stop/time": {
            "shape": (1,),
            "dtype": "float64",
        },
        # ---
        # --- dataset: entry/run_info/stop/uid ---
        # ---
        "entry/run_info/stop/uid": {
            "shape": (1,),
            "dtype": "O",
        },
    }

    # Verify file contents
    verify_nexus_file(nx_file_path, expected_structure, expected_data)

    # Remove the nexus file after successful validation
    clean_up(nx_file_path)
    # Remove the callback file after successful creation
    clean_up(callback_file_path)


if __name__ == "__main__":
    # Execute all test cases in the script when run directly.
    # import pytest

    pytest.main([__file__])
