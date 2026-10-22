from pathlib import Path
from bluesky_nexus.tiled import HdfWriterSubscription


from bluesky_nexus.logger import LOGGER
from tiled.client import container
from tiled.client.container import Container


def run_tiled_dispatcher(root_output_directory: Path, client: Container) -> None:
    """Start a subscription to a tiled client and write .nxs files for each new
    finished run, blocks the thread.

    Only entries with the structure of bluesky-tiled-plugins will be parsed.

    Parameters
    ----------
    root_output_directory : int
        The root directory that the nexus writer should write files to.
    client : Container
        A connected tiled container.
    """
    LOGGER.info(
        "Subscribing to tiled container '%s'.",
        container,
    )
    subscription = client.subscribe()
    subscription.child_created.add_callback(HdfWriterSubscription(root_output_directory))

    # ---------------------------------------------------------------------------
    # Create and start the RemoteDispatcher
    # ---------------------------------------------------------------------------

    LOGGER.info("Tiled subscription ready. Press Ctrl+C to stop.")

    try:
        subscription.start()
    except KeyboardInterrupt:
        LOGGER.warning("Shutdown requested by user (Ctrl+C), disconnecting from tiled.")
        try:
            subscription.disconnect()
        except Exception:
            LOGGER.exception("Error stopping tiled subscription cleanly.")
        LOGGER.info("Tiled subscription stopped.")
