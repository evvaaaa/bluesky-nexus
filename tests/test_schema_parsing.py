import time
from pathlib import Path, PurePath
from pprint import pformat

from bluesky import RunEngine
from bluesky import plans as bp
from nexusformat import nexus
from ophyd_async.sim import SimPointDetector

from bluesky_nexus import NexusDevice

from . import load_only_generated_nexus_file


def test_example_schema_and_manual_schema_with_equivalence(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>-channel-1-value": None,
            "<name>-channel-2-value": None,
        }
    )
    class SimPointDetectorWithSchema(SimPointDetector):
        pass

    RE_directly_subscribed(
        bp.count(
            [
                SimPointDetectorWithSchema(None, name="sim_point_detector_with_schema"),
                SimPointDetector(None, name="sim_point_detector_without_schema"),
            ],
            num=3,
        )
    )  # type: ignore

    time.sleep(0.1)

    loaded = load_only_generated_nexus_file(tmpdir)
    sim_point_detector_with_some_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]
    sim_point_detector_with_without_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]

    assert (
        list(sim_point_detector_with_some_schema)
        == list(sim_point_detector_with_without_schema)
        == [
            "channel-1-mode",
            "channel-1-value",
            "channel-2-mode",
            "channel-2-value",
            "channel-3-mode",
            "channel-3-value",
        ]
    )


def test_simple_nx_detector(
    RE_directly_subscribed: RunEngine,
    tmpdir: Path,
):
    @NexusDevice.from_dictionary(
        {
            "nx_class": "NXobject",
            "<name>-channel-1-value": None,
            "<name>-channel-2-value": None,
        }
    )
    class SimPointDetectorWithSchema(SimPointDetector):
        pass

    RE_directly_subscribed(
        bp.count(
            [
                SimPointDetectorWithSchema(None, name="sim_point_detector_with_schema"),
                SimPointDetector(None, name="sim_point_detector_without_schema"),
            ],
            num=3,
        )
    )  # type: ignore

    time.sleep(0.1)

    loaded = load_only_generated_nexus_file(tmpdir)
    sim_point_detector_with_some_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]
    sim_point_detector_with_without_schema = loaded["entry"]["primary"][
        "sim_point_detector_with_schema"
    ]

    assert (
        list(sim_point_detector_with_some_schema)
        == list(sim_point_detector_with_without_schema)
        == [
            "channel-1-mode",
            "channel-1-value",
            "channel-2-mode",
            "channel-2-value",
            "channel-3-mode",
            "channel-3-value",
        ]
    )
