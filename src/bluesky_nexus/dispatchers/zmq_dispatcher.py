"""Service for running the Bluesky NeXus RemoteDispatcher via ZeroMQ.

This module provides the implementation for the `zmq` data-source option of
the Bluesky NeXus writer service. It is typically invoked through:

    python -m bluesky_nexus --source zmq ...

The function `run_zmq_dispatcher` is responsible for:

- Resolving configuration from CLI arguments or environment variables.
- Validating the required inputs.
- Initializing NeXus logging.
- Creating a `NexusWriter` callback.
- Starting a Bluesky `RemoteDispatcher` that receives documents over ZeroMQ
  and forwards them into the writer.

---------------------------------------------------------------------------
Mandatory configuration
---------------------------------------------------------------------------

| Environment Variable     | CLI Argument   | Description                      |
|--------------------------|----------------|----------------------------------|
| `_ZMQ_IP`                | `--zmq-ip`     | ZeroMQ publisher IP address      |
| `_ZMQ_PORT`              | `--zmq-port`   | ZeroMQ publisher port            |
| `_NX_FILE_DIR_PATH`      | `--nx-dir`     | Directory for NeXus output files |
| `_NX_LOG_FILE_DIR_PATH`  | `--log-dir`    | Directory for NeXus log files    |

Optional:

| Environment Variable         | CLI Argument       | Description                   |
|------------------------------|--------------------|-------------------------------|
| `_OPHYD_CPT_NAME_DELIMITER`  | `--cpt-delimiter`  | Delimiter for ophyd cpt names |

Notes
-----
The dispatcher simply forwards documents to the given callback.
"""

import os

from bluesky.callbacks.zmq import RemoteDispatcher

from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import LogLevel, setup_nx_logger


def run_zmq_dispatcher(args) -> None:
    """Start a Bluesky RemoteDispatcher using ZeroMQ.

    This function is executed when the user selects the ``zmq`` data-source
    from the top-level CLI (``python -m bluesky_nexus zmq``).

    Responsibilities:

    1. Resolve configuration values from CLI arguments, with optional
       fallbacks to environment variables.
    2. Validate all required parameters.
    3. Initialize logging for the NexusWriter (console + rotating file logs).
    4. Instantiate the `NexusWriter` callback.
    5. Instantiate and start a ZeroMQ-backed `RemoteDispatcher`, subscribing
       the NexusWriter to Bluesky documents.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments for the ZeroMQ subparser. Expected attributes:

        Required:
            - zmq_ip : str or None
                IP address of the ZeroMQ publisher.
            - zmq_port : str or None
                Port of the ZeroMQ publisher.
            - nx_dir : str or None
                Directory where NeXus files will be written.
            - log_dir : str or None
                Directory where NeXus log files will be stored.

        Optional:
            - cpt_delimiter : str or None
                Custom ophyd component name delimiter.

    Environment Variable Fallbacks
    ------------------------------
    CLI arguments take precedence. If not provided, the following environment
    variables supply fallback values:

        _ZMQ_IP                   → --zmq-ip
        _ZMQ_PORT                 → --zmq-port
        _NX_FILE_DIR_PATH         → --nx-dir
        _NX_LOG_FILE_DIR_PATH     → --log-dir
        _OPHYD_CPT_NAME_DELIMITER → --cpt-delimiter

    Raises
    ------
    ValueError
        If any required configuration value is missing.

    KeyboardInterrupt
        Gracefully stops the dispatcher when Ctrl+C is pressed.

    Notes
    -----
    - The dispatcher runs until interrupted (Ctrl+C).
    - On shutdown, it attempts a clean dispatcher termination.
    """
    # ---------------------------------------------------------------------------
    # Resolve configuration with fallback to environment variables if CLI absent
    # ---------------------------------------------------------------------------
    zmq_ip = args.zmq_ip or os.environ.get("_ZMQ_IP")
    zmq_port = args.zmq_port or os.environ.get("_ZMQ_PORT")
    nx_dir = args.nx_dir or os.environ.get("_NX_FILE_DIR_PATH")
    log_dir = args.log_dir or os.environ.get("_NX_LOG_FILE_DIR_PATH")
    cpt_delimiter = args.cpt_delimiter or os.environ.get("_OPHYD_CPT_NAME_DELIMITER")

    # ---------------------------------------------------------------------------
    # Validation of required inputs
    # ---------------------------------------------------------------------------
    if not zmq_ip:
        raise ValueError("Missing ZeroMQ IP (--zmq-ip or env. var. _ZMQ_IP).")

    if not zmq_port:
        raise ValueError("Missing ZeroMQ port (--zmq-port or env. var. _ZMQ_PORT).")

    if not nx_dir:
        raise ValueError(
            "Missing NeXus file directory (--nx-dir or env. var. _NX_FILE_DIR_PATH)."
        )

    if not log_dir:
        raise ValueError(
            "Missing NeXus log directory "
            "(--log-dir or env. var. _NX_LOG_FILE_DIR_PATH)."
        )

    print(f"NeXus output directory: {nx_dir}")
    print(f"NeXus log directory:    {log_dir}")

    # ---------------------------------------------------------------------------
    # Initialize NexusWriter Logging
    # ---------------------------------------------------------------------------
    setup_nx_logger(
        console_level=LogLevel.ERROR,
        file_level=LogLevel.DEBUG,
        log_file_dir_path=log_dir,
        log_file_name="nx_log.log",
        log_format=None,
        max_file_size=10 * 1024 * 1024,
        backup_count=5,
        enable_console=True,
        enable_file=True,
    )

    # ---------------------------------------------------------------------------
    # Initialize NexusWriter callback
    # ---------------------------------------------------------------------------
    if cpt_delimiter:
        print(f"Using ophyd component delimiter: {cpt_delimiter}")
        writer = NexusWriter(nx_file_dir_path=nx_dir, cpt_name_delimiter=cpt_delimiter)
    else:
        writer = NexusWriter(nx_file_dir_path=nx_dir)

    # ---------------------------------------------------------------------------
    # Create and start the RemoteDispatcher
    # ---------------------------------------------------------------------------
    address = f"{zmq_ip}:{zmq_port}"
    print(f"Connecting to ZMQ publisher at {address}")

    dispatcher = RemoteDispatcher(address)
    dispatcher.subscribe(writer)
    print("ZMQ RemoteDispatcher ready. Press Ctrl+C to stop.")

    try:
        dispatcher.start()
    except KeyboardInterrupt:
        print("Shutdown requested.")
        try:
            dispatcher.stop()
        except Exception:
            pass
        print("ZMQ dispatcher stopped.")
