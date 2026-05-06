"""ZeroMQ-based RemoteDispatcher service for Bluesky NeXus writing.

This module implements the ZeroMQ backend for the ``bluesky_nexus`` service.
It consumes Bluesky documents from a ZeroMQ publisher and forwards them to
:class:`NexusWriter`, which produces NeXus-compatible HDF5 files.

Configuration may be provided through CLI arguments or environment variables.
CLI arguments take precedence over environment variables.

---------------------------------------------------------------------------
Required Configuration
---------------------------------------------------------------------------

| CLI Argument            | Environment Variable   | Description                       |
|-------------------------|------------------------|-----------------------------------|
| --zmq-ip                | _ZMQ_IP                | ZeroMQ publisher IP address       |
| --zmq-port              | _ZMQ_PORT              | ZeroMQ publisher port             |
| --nx-file-root-dir-path | _NX_FILE_ROOT_DIR_PATH | Root dir for NeXus output files   |

---------------------------------------------------------------------------
Optional Configuration
---------------------------------------------------------------------------

| CLI Argument     | Environment Variable       | Description                      |
|------------------|----------------------------|----------------------------------|
| --cpt-delimiter  | _OPHYD_CPT_NAME_DELIMITER  | Custom ophyd component delimiter |

---------------------------------------------------------------------------
Runtime Behaviour
---------------------------------------------------------------------------

1. Resolve configuration via CLI or environment fallback.
2. Validate that all required values are present.
3. Validate the NeXus output directory.
4. Instantiate :class:`NexusWriter`.
5. Create a ZeroMQ-backed :class:`RemoteDispatcher`.
6. Subscribe the writer to the dispatcher.
7. Consume Bluesky documents until interrupted.
8. Shut down the dispatcher cleanly.
"""

import os
from pathlib import Path

from bluesky.callbacks.zmq import RemoteDispatcher as ZMQDispatcher

from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.common.validation_utils import validate_directory


def run_zmq_dispatcher(args) -> None:
    """Start the ZeroMQ-based Bluesky RemoteDispatcher.

    This function is invoked by the CLI entry point after argument parsing.
    It extracts the resolved configuration from ``args`` (with environment
    variable fallbacks handled at runtime), validates the required values,
    instantiates the :class:`NexusWriter`, and starts a ZeroMQ-backed
    :class:`RemoteDispatcher`.

    All details about configuration, required arguments, environment
    variables, and runtime behaviour are documented in the module docstring.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments for the ZeroMQ backend.

    Raises
    ------
    ValueError
        If one or more required configuration values (IP, port,
        or NeXus output directory) are missing.
    """
    # ---------------------------------------------------------------------------
    # Resolve configuration with fallback to environment variables if CLI absent
    # ---------------------------------------------------------------------------
    zmq_ip = args.zmq_ip or os.environ.get("_ZMQ_IP")
    zmq_port = args.zmq_port or os.environ.get("_ZMQ_PORT")
    nx_file_root_dir_path = args.nx_file_root_dir_path or os.environ.get("_NX_FILE_ROOT_DIR_PATH")
    cpt_delimiter = args.cpt_delimiter or os.environ.get("_OPHYD_CPT_NAME_DELIMITER")

    # ---------------------------------------------------------------------------
    # Validation of required inputs
    # ---------------------------------------------------------------------------
    if not zmq_ip:
        raise ValueError("Missing ZeroMQ IP (--zmq-ip or env. var. _ZMQ_IP).")

    if not zmq_port:
        raise ValueError("Missing ZeroMQ port (--zmq-port or env. var. _ZMQ_PORT).")

    if not nx_file_root_dir_path:
        raise ValueError(
            "Missing NeXus file root directory "
            "(--nx-file-root-dir-path or env. var. _NX_FILE_ROOT_DIR_PATH)."
        )

    # ---------------------------------------------------------------------------
    # Validate NeXus file output directory
    # ---------------------------------------------------------------------------
    nx_dir: Path = validate_directory(nx_file_root_dir_path, "NeXus file root directory")
    logger.info("Validated NeXus root directory: %s", nx_dir)

    # ---------------------------------------------------------------------------
    # Initialize NexusWriter callback
    # ---------------------------------------------------------------------------
    if cpt_delimiter:
        logger.info("Using ophyd component delimiter: %s", cpt_delimiter)
        writer = NexusWriter(nx_file_root_dir_path=nx_dir, cpt_name_delimiter=cpt_delimiter)
    else:
        writer = NexusWriter(nx_file_root_dir_path=nx_dir)

    # ---------------------------------------------------------------------------
    # Create and start the RemoteDispatcher
    # ---------------------------------------------------------------------------
    address = f"{zmq_ip}:{zmq_port}"
    logger.info("Connecting to ZeroMQ publisher at %s", address)

    dispatcher = ZMQDispatcher(address)
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
