"""Tests that if you ran the tutorials now you would get the same as the tutorials claim.

Good for keeping docs up to date with changes.
"""

from pathlib import Path
from runpy import run_path
from typing import Any

import numpy as np
import pytest

import bluesky_nexus

from . import load_only_generated_nexus_file

TUTORIAL_FILES_DIRECTORY = Path(bluesky_nexus.__file__).parent.parent.parent / "docs" / "_static"


@pytest.fixture(autouse=True)
def change_local_directory_to_tmpdir(tmpdir: Path, monkeypatch: pytest.MonkeyPatch):
    # Allows for tutorial files to write to "." but we get it in tmpdir in tests.
    monkeypatch.chdir(tmpdir)


@pytest.fixture
def globals_with_runengine() -> dict[str, Any]:
    return run_path(
        f"{TUTORIAL_FILES_DIRECTORY}/tutorials/tutorial_setting_up_callbacks.py",
        run_name="__main__",
    )


def test_tutorial_simple_device_count(
    tmpdir: Path, capsys: pytest.CaptureFixture, globals_with_runengine: dict[str, Any]
):
    run_path(
        f"{TUTORIAL_FILES_DIRECTORY}/tutorials/tutorial_simple_device_count.py",
        run_name="__main__",
        init_globals=globals_with_runengine,
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    captured = capsys.readouterr().out
    assert (
        "devices:NXinstrument\n        syn_axis:NXsubentry\n          @nxclass = 'NXsubentry'"
    ) in captured

    assert list(loaded["entry"]["primary"]["devices"]) == ["syn_axis"]


def test_tutorial_1(tmpdir: Path, globals_with_runengine: dict[str, Any]):
    globals = run_path(
        f"{TUTORIAL_FILES_DIRECTORY}/tutorials/tutorial1_devices.py",
        run_name="__main__",
        init_globals=globals_with_runengine,
    )
    globals = run_path(
        f"{TUTORIAL_FILES_DIRECTORY}/tutorials/tutorial1_plan.py",
        run_name="__main__",
        init_globals=globals,
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    assert list(loaded["entry"]["primary"]["stream_info"]["descriptor"]["object_keys"]) == ["pgm"]

    assert list(loaded["entry"]["primary"]["devices"]) == ["pgm"]
    pgm = loaded["entry"]["primary"]["devices"]["pgm"]
    assert list(pgm) == [
        "cff",
        "diff_order",
        "energy",
        "energy_acceleration_time",
        "energy_velocity",
        "exit_slit",
        "exit_slit_acceleration_time",
        "exit_slit_exit_slit_branch",
        "exit_slit_velocity",
        "grating",
        "grating_number",
        "harmonic",
        "maxumum_energy",
        "minimum_energy",
        "mirror2_translation",
        "mirror2_translation_acceleration_time",
        "mirror2_translation_velocity",
        "phi_angle",
        "phi_enabled",
        "psi_angle",
        "psi_enabled",
        "sweep_offset",
    ]

    assert str(pgm["harmonic"]["value"]) == "3rd Harmonic"
    assert list(pgm["energy"]["value"]) == [
        np.float64(0.0),
        np.float64(546.1111111111111),
        np.float64(547.2222222222222),
        np.float64(548.3333333333334),
        np.float64(549.4444444444445),
        np.float64(550.5555555555555),
        np.float64(551.6666666666666),
        np.float64(552.7777777777778),
        np.float64(553.8888888888889),
        np.float64(555.0),
    ]
