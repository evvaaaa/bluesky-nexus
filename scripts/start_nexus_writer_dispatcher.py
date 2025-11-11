"""Start a Bluesky RemoteDispatcher and NeXus writer service.

This module launches a standalone process that listens to a Bluesky ZeroMQ
publisher and writes NeXus files for all incoming documents. It uses the
`NexusWriter` from `bluesky_nexus` and automatically resolves the output
directory via `get_nx_file_dir_path()`. It also configures an optional,
high-granularity NeXus logging system.

Environment variables control the runtime behavior:

- **ZMQ_IP** (required): IP address of the ZeroMQ publisher.
- **ZMQ_PORT** (required): Port of the ZeroMQ publisher.
- **NX_FILE_DIR_PATH** (implicit): Resolved via `get_nx_file_dir_path()`.
- **NX_LOG_FILE_DIR_PATH** (implicit): Resolved via `get_nx_log_file_dir_path()`.
- **OPHYD_CPT_NAME_DELIMITER** (optional): Custom delimiter for addressing
  component names inside Bluesky documents. If not set, ``_`` (underscore)
  is assumed as the default by the writer.

Logging Configuration:

1. **Logging Initialization**
   - A NeXus logger is initialized via ``setup_nx_logger`` with optional
     console and file handlers.
   - Logging supports configurable formatting, separate verbosity levels for
     console and file output, log rotation (max file size + backup count),
     and user-selectable disabling/enabling of either handler.
   - When enabled, the log file is written into the directory returned by
     ``get_nx_log_file_dir_path()``.

Workflow:

1. Read and validate all required environment variables.
2. Configure the NeXus logging system using ``setup_nx_logger``.
3. Instantiate the `NexusWriter`, optionally applying the component-name delimiter.
4. Construct a `RemoteDispatcher` using the given ZeroMQ IP/port.
5. Subscribe the writer to the dispatcher.
6. Start the dispatcher event loop and continuously process incoming Bluesky
   documents until interrupted (Ctrl+C).

Run this module as a script to launch and maintain the NeXus writer service.
"""

import os

from bluesky.callbacks.zmq import RemoteDispatcher

from bluesky_nexus.bluesky_nexus_paths import (
    get_nx_file_dir_path,
    get_nx_log_file_dir_path,
)
from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import LogLevel, setup_nx_logger


def main():
    """Start the NeXus writer service.

    Reads and validates required environment variables, configures NeXus
    logging, instantiates a `NexusWriter`, and connects it to a Bluesky
    `RemoteDispatcher` using the configured ZeroMQ address. Once started,
    the dispatcher listens for incoming Bluesky documents and writes NeXus
    files until interrupted (Ctrl+C).
    """
    # Read env vars
    ophyd_cpt_name_delimiter = os.environ.get("OPHYD_CPT_NAME_DELIMITER")
    zmq_ip = os.environ.get("ZMQ_IP")
    zmq_port = os.environ.get("ZMQ_PORT")

    nx_file_dir_path = get_nx_file_dir_path()
    nx_log_file_dir_path = get_nx_log_file_dir_path()

    # Validate env vars
    if not zmq_ip:
        raise EnvironmentError("Environment variable 'ZMQ_IP' is not set.")
    if not zmq_port:
        raise EnvironmentError("Environment variable 'ZMQ_PORT' is not set.")
    if not nx_file_dir_path:
        raise EnvironmentError("'NX_FILE_DIR_PATH' missing or invalid.")
    if not nx_log_file_dir_path:
        raise EnvironmentError("'NX_LOG_FILE_DIR_PATH' missing or invalid.")

    print(f"NeXus output directory: {nx_file_dir_path}")

    # This is an optional setup for the NeXus logger. If not configured,
    # logging to a file is disabled by default. The logger supports separate
    # configuration for console and file output, with options for log rotation,
    # formatting, and enabling/disabling handlers.
    setup_nx_logger(
        console_level=LogLevel.ERROR,
        file_level=LogLevel.DEBUG,
        log_file_dir_path=nx_log_file_dir_path,
        log_file_name="nx_log.log",
        log_format=None,  # Uses default format if None
        max_file_size=10 * 1024 * 1024,  # 10 MB
        backup_count=5,
        enable_console=True,
        enable_file=True,
    )
    if ophyd_cpt_name_delimiter:
        print(f"Using ophyd CPT name delimiter: {ophyd_cpt_name_delimiter}")

        # Create Nexus writer
        nexus_writer = NexusWriter(
            nx_file_dir_path=nx_file_dir_path,
            cpt_name_delimiter=ophyd_cpt_name_delimiter,
        )
    else:
        # Create Nexus writer
        nexus_writer = NexusWriter(nx_file_dir_path=nx_file_dir_path)

    # Create RemoteDispatcher
    address = f"{zmq_ip}:{zmq_port}"
    print(f"ZMQ remote dispatcher connecting to {address}")
    remote_dispatcher = RemoteDispatcher(address)
    remote_dispatcher.subscribe(nexus_writer)

    print(
        "Subscription to remote dispatcher active. Ready to write NeXus files.\n"
        "Press Ctrl+C to exit safely."
    )

    try:
        remote_dispatcher.start()
    except KeyboardInterrupt:
        print("Exiting…")
        try:
            remote_dispatcher.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
