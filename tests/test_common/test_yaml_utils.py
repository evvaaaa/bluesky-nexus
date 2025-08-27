"""
Module:              test_yaml_utils.py.

Description:
    This module contains pytest-based unit tests for verifying the functionality
    of the `read_yaml` function from `yaml_utils.py`. It also checks the presence
    of necessary test data files and directories.

Tested functionality:
    - Existence of the test data directory (`data`)
    - Existence of YAML test files:
        - non-empty YAML file (`not_empty.yml`)
        - empty YAML file (`empty.yml`)
    - Behavior of `read_yaml()` under various conditions:
        - Called without arguments (expects TypeError)
        - Called with empty string path (expects FileNotFoundError)
        - Called with wrong parameter type (expects OSError)
        - Called with too many arguments (expects TypeError)
        - Reading an empty YAML file returns None
        - Reading a non-empty YAML file returns the expected dictionary

Test data directory:
    - `data/`

Test files:
    - `data/not_empty.yml` (contains valid YAML content)
    - `data/empty.yml` (empty YAML file)
"""

import os

import pytest

from bluesky_nexus.common.yaml_utils import read_yaml

# Define path to data folder
data_folder: str = os.path.join(os.path.dirname(__file__), "data")

# Define path to non empty y(a)ml-file serving as "test data"
file_name: str = "not_empty.yml"
file_path: str = os.path.join(data_folder, file_name)

# Define path to empty y(a)ml-file serving as "test data"
file_name_empty_file: str = "empty.yml"
file_path_empty_file: str = os.path.join(data_folder, file_name_empty_file)


# Test if "data_folder" is pointing to a folder
def test_data_dir() -> None:
    """Test that the data directory exists and is a directory."""
    assert os.path.isdir(data_folder)


# Test if "file_path" is pointing to a file
def test_not_empty_file_exists() -> None:
    """Test that the non-empty YAML test file exists."""
    assert os.path.isfile(file_path)


# Test if "file_path_empty_file" is pointing to a file
def test_empty_file_exists() -> None:
    """Test that the empty YAML test file exists."""
    assert os.path.isfile(file_path_empty_file)


# Test read_yaml if missing file path parameter
def test_read_yaml_no_path() -> None:
    """Test read_yaml() without any arguments.

    read_yaml() called without any path argument should raise a
    TypeError.
    """
    # pylint: disable=no-value-for-parameter
    with pytest.raises(TypeError):
        _: list | dict | None = read_yaml()  # type: ignore[call-arg]


# Test read_yaml if empty file path parameter
def test_read_yaml_empty_path() -> None:
    """Test read_yaml() with an empty string path.

    read_yaml() called with an empty string path should raise
    FileNotFoundError.
    """
    with pytest.raises(FileNotFoundError):
        _: list | dict | None = read_yaml("")


# Test read_yaml if parameter is not a string
def test_read_yaml_wrong_param_type() -> None:
    """Test read_yaml() with wrong argument type.

    read_yaml() called with a non-string parameter should raise an
    OSError.
    """
    with pytest.raises(OSError):
        _: list | dict | None = read_yaml(123)  # type: ignore[arg-type]


# Test read_yaml if wrong number of parameters
def test_read_yaml_wrong_param_number() -> None:
    """Test read_yaml() with wrong argument number.

    read_yaml() called with more than one argument should raise a
    TypeError.
    """
    # pylint: disable=too-many-function-args,arguments-out-of-order
    with pytest.raises(TypeError):
        _: list | dict | None = read_yaml(file_path, file_path)  # type: ignore[call-arg]


# Test read_yaml if y(a)ml-file is empty
def test_read_yaml_empty_file() -> None:
    """Test that read of empty yml file returns None.

    read_yaml() should return None when called with an empty YAML file.
    """
    actual: list | dict | None = read_yaml(file_path_empty_file)
    assert actual is None


# Test read_yaml if y(a)ml-file is not empty
def test_read_yaml() -> None:
    """Test that read_yaml() returns the expected dictionary.

    This test uses a non-empty YAML file to verify the output matches
    the expected dictionary.
    """
    actual: list | dict | None = read_yaml(file_path)
    expected = {
        "nx_model": "NXmonochromatorModel",
        "nx_schema": "nx_test_mono_schema",
        "energy": {
            "nxclass": "NX_FLOAT",
            "value": "$post-run:events:en",
            "dtype": "float64",
            "attrs": {"units": "eV"},
        },
        "grating": {
            "nxclass": "NXgrating",
            "diffraction_order": {
                "nxclass": "NX_INT",
                "value": "$pre-run-cpt:grating",
                "dtype": "int32",
            },
        },
    }
    assert actual == expected


if __name__ == "__main__":
    # Execute all test cases in the script when run directly.
    pytest.main([__file__])
