"""Tests that if you ran the examples now you would get the same as the tutorials claim.

Good for keeping docs up to date with changes.
"""

from pathlib import Path
from runpy import run_path
from typing import Any

import numpy as np
import pytest

import bluesky_nexus

from . import load_only_generated_nexus_file

EXAMPLE_FILES_DIRECTORY = (
    Path(bluesky_nexus.__file__).parent.parent.parent / "docs" / "_static" / "examples"
)


@pytest.fixture(autouse=True)
def change_local_directory_to_tmpdir(tmpdir: Path, monkeypatch: pytest.MonkeyPatch):
    # Allows for tutorial files to write to "." but we get it in tmpdir in tests.
    monkeypatch.chdir(tmpdir)


@pytest.fixture(scope="function")
def globals_with_runengine() -> dict[str, Any]:
    return run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_setting_up_run_engine.py",
        run_name="__main__",
    )


def test_example_simple_device_count(
    tmpdir: Path, capsys: pytest.CaptureFixture, globals_with_runengine: dict[str, Any]
):
    run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_simple_device_count.py",
        run_name="__main__",
        init_globals=globals_with_runengine,
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    captured = capsys.readouterr().out
    assert (
        "devices:NXinstrument\n        syn_axis:NXsubentry\n          @nxclass = 'NXsubentry'"
    ) in captured

    assert list(loaded["entry"]["primary"]["devices"]) == ["syn_axis"]


def test_example_mono_1(tmpdir: Path, globals_with_runengine: dict[str, Any]):
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_mono_1_devices.py",
        run_name="__main__",
        init_globals=globals_with_runengine,
    )
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_mono_plan.py",
        run_name="__main__",
        init_globals=globals,
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    assert list(loaded["entry"]["primary"]["stream_info"]["descriptor"]["object_keys"]) == ["pgm"]

    assert list(loaded["entry"]["primary"]["devices"]) == ["pgm"]
    pgm = loaded["entry"]["primary"]["devices"]["pgm"]
    assert pgm.nxclass == "NXsubentry"
    assert list(pgm) == [
        "cff",
        "diff_order",
        "energy_readback",
        "energy_setpoint",
        "energy_velocity",
        "exit_slit_selected_branch",
        "exit_slit_value",
        "grating_number",
        "grating_selection",
        "grating_translation",
        "harmonic",
        "maxumum_energy",
        "minimum_energy",
        "mirror2_translation",
        "phi_enabled",
        "phi_value",
        "psi_enabled",
        "psi_value",
    ]

    assert str(pgm["harmonic"]["value"]) == "3rd Harmonic"
    assert list(pgm["energy_setpoint"]["value"]) == [
        np.float64(545.0),
        np.float64(545.5555555555555),
        np.float64(546.1111111111111),
        np.float64(546.6666666666666),
        np.float64(547.2222222222222),
        np.float64(547.7777777777778),
        np.float64(548.3333333333334),
        np.float64(548.8888888888889),
        np.float64(549.4444444444445),
        np.float64(550.0),
    ]


def test_example_mono_2(tmpdir: Path, globals_with_runengine: dict[str, Any]):
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_mono_1_devices.py",
        run_name="__main__",
        init_globals=globals_with_runengine,
    )
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_mono_2_devices.py",
        run_name="__main__",
        init_globals=globals,
    )
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_mono_plan.py",
        run_name="__main__",
        init_globals=globals,
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    assert list(loaded["entry"]["primary"]["stream_info"]["descriptor"]["object_keys"]) == ["pgm"]

    assert list(loaded["entry"]["primary"]["devices"]) == ["pgm"]
    pgm = loaded["entry"]["primary"]["devices"]["pgm"]
    assert pgm.nxclass == "NXmonochromator"
    assert list(pgm) == [
        "constant_fixed_focus",
        "diffraction_order",
        "energy",
        "energy_setpoint",
        "energy_velocity",
        "exit_slit",
        "filters",
        "grating",
        "grating_number",
        "grating_translation",
        "harmonic",
        "maxumum_energy",
        "minimum_energy",
        "mirror",
        "transformations",
    ]


def test_example_keithley_1():
    run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_keithley_1_device.py",
        run_name="__main__",
    )


def test_keithley_nexus_structure():
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_keithley_1_device.py",
        run_name="__main__",
    )
    globals = run_path(
        f"{EXAMPLE_FILES_DIRECTORY}/example_keithley_2_device.py",
        run_name="__main__",
        init_globals=globals,
    )
