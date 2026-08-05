"""ZeroMQ-based RemoteDispatcher service for Bluesky NeXus writing.

This module implements the ZeroMQ backend for the ``bluesky_nexus`` service.
It consumes Bluesky documents from a ZeroMQ publisher and forwards them to
:class:`NexusWriter`, which produces NeXus-compatible HDF5 files.
"""

from pathlib import Path

from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.nx_writer import NexusWriter


def run_zmq_dispatcher(root_output_directory: Path, zmq_ip: str, zmq_port: int) -> None:
    """Start the ZeroMQ-based Bluesky RemoteDispatcher.

    This method initializes a callback class with the selected output directory,
    and then subscribes to it over zmq.

    Parameters
    ----------
    root_output_directory : int
        The root directory that the nexus writer should write files to.
    zmq_ip : str
        The ip of the zmq stream to read from.
    zmq_port : int
        The port of the zmq stream to read from.
    """
    try:
        from bluesky.callbacks.zmq import RemoteDispatcher
    except Exception as exception:
        raise RuntimeError(
            "Could not import the zmq `RemoteDispatcher` from bluesky. "
            "Did you install `bluesky-nexus-callback[zmq]`?"
        ) from exception

    writer = NexusWriter(root_output_directory=root_output_directory)

    # ---------------------------------------------------------------------------
    # Create and start the RemoteDispatcher
    # ---------------------------------------------------------------------------
    address = f"{zmq_ip}:{zmq_port}"
    logger.info("Connecting to ZeroMQ publisher at %s", address)

    dispatcher = RemoteDispatcher(address)
    dispatcher.subscribe(writer)

    logger.info("ZMQ RemoteDispatcher ready. Press Ctrl+C to stop.")

    try:
        dispatcher.start()
    except KeyboardInterrupt:
        logger.warning("Shutdown requested by user (Ctrl+C).")
        try:
            dispatcher.stop()
        except Exception:
            logger.exception("Error stopping ZMQ dispatcher cleanly.")
        logger.info("ZMQ dispatcher stopped.")
