from typing import Container
from bluesky import plans as bp
from pathlib import Path
from ophyd_async.sim import SimPointDetector

from bluesky_nexus.device._nx_device import NxDevice
from bluesky_nexus.schema.nx_base_class import NxBaseClass
from . import load_only_generated_nexus_file
from bluesky import RunEngine


def test_simple_nx_detector(
    RE_subscribed_to_tiled: RunEngine,
    tiled_client: Container,
    tmpdir: Path,
) -> None:
    dictionary = {
        "$nxclass": "NXdetector",
        "data": {"data_key": "channel-1-value"},
    }

    class NxSimPointDetector(NxDevice, SimPointDetector):
        BLUESKY_NEXUS_BASE_CLASS = NxBaseClass.from_dictionary(dictionary)

    detector = NxSimPointDetector(None, name="detector")
    RE_subscribed_to_tiled(
        bp.count(
            [detector],
            num=3,
        )
    )

    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["streams"]["primary"]["devices"][
        "detector"
    ]

    assert list(loaded) == [
        "channel_1_mode",
        "channel_2_mode",
        "channel_2_value",
        "channel_3_mode",
        "channel_3_value",
        "data",
    ]
    assert list(loaded["data"]) == ["time", "value"]
    assert list(loaded["data"]["value"]) == [290, 290, 290]


def test_foobar():
    from bluesky import RunEngine
    import bluesky.plans as bp
    from bluesky_tiled_plugins import TiledWriter
    from tiled.server import SimpleTiledServer
    from tiled.client import from_uri
    from ophyd.sim import det
    from ophyd.sim import hw

    # Initialize the Tiled server and client
    save_path = "/path/to/save/detector_data"
    tiled_server = SimpleTiledServer(readable_storage=[save_path])
    tiled_client = from_uri(tiled_server.uri)

    # Initialize the RunEngine and subscribe TiledWriter
    RE = RunEngine()
    tw = TiledWriter(tiled_client, batch_size=1)
    RE.subscribe(tw)

    # Run an experiment collecting internal data
    print("here")
    (uid,) = RE(bp.count([det], 3))
    data = tiled_client[uid]["primary/det"].read()
    print("here")

    # Run an experiment collecting external data
    print("here")
    (uid,) = RE(bp.count([hw(save_path=save_path).img], 2))
    print("here")
    data = tiled_client[uid]["primary/img"].read()
