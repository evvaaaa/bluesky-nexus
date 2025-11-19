"""Service for running the Bluesky NeXus RemoteDispatcher.

This module defines a CLI entry point that can be invoked via:

    python -m bluesky_nexus

Arguments may be provided either explicitly on the command line or implicitly
via environment variables. If neither provides a required value, an error
is raised.

### Mandatory Inputs

| Environment Variable     | CLI Argument   | Description                       |
|--------------------------|----------------|-----------------------------------|
| `_ZMQ_IP`                | `--zmq-ip`     | ZeroMQ publisher IP address       |
| `_ZMQ_PORT`              | `--zmq-port`   | ZeroMQ publisher port             |
| `_NX_FILE_DIR_PATH`      | `--nx-dir`     | Directory for NeXus output files  |
| `_NX_LOG_FILE_DIR_PATH`  | `--log-dir`    | Directory for NeXus log files     |

### Optional Input

| Environment Variable         | CLI Argument       | Description                   |
|------------------------------|--------------------|-------------------------------|
| `_OPHYD_CPT_NAME_DELIMITER`  | `--cpt-delimiter`  | Delimiter for ophyd cpt names |
"""

import argparse
import os

from bluesky.callbacks.zmq import RemoteDispatcher

from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import LogLevel, setup_nx_logger


def run_dispatcher() -> None:
    """Start NeXus RemoteDispatcher service.

    Parse arguments (CLI + environment), validate them, and start the
    Bluesky → NeXus RemoteDispatcher service.

    This function has no parameters because configuration is handled
    through argparse and environment variables.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Start a Bluesky RemoteDispatcher that listens on a ZeroMQ address "
            "and generates/writes NeXus files (.nxs) based on Bluesky documents."
        )
    )

    # -----------------------------------------------------------
    # CLI arguments with defaults drawn from environment variables
    # -----------------------------------------------------------

    parser.add_argument(
        "--zmq-ip",
        type=str,
        default=os.environ.get("_ZMQ_IP"),
        help="IP address of the ZeroMQ publisher (mandatory input) "
        "(default: from _ZMQ_IP env var)",
    )

    parser.add_argument(
        "--zmq-port",
        type=str,
        default=os.environ.get("_ZMQ_PORT"),
        help="Port of the ZeroMQ publisher (mandatory input) "
        "(default: from _ZMQ_PORT env var)",
    )

    parser.add_argument(
        "--nx-dir",
        type=str,
        default=os.environ.get("_NX_FILE_DIR_PATH"),
        help="Directory for NeXus files (mandatory input) "
        "(default: from _NX_FILE_DIR_PATH env var)",
    )

    parser.add_argument(
        "--log-dir",
        type=str,
        default=os.environ.get("_NX_LOG_FILE_DIR_PATH"),
        help="Directory for NeXus log files (mandatory input) "
        "(default: from _NX_LOG_FILE_DIR_PATH env var)",
    )

    parser.add_argument(
        "--cpt-delimiter",
        type=str,
        default=os.environ.get("_OPHYD_CPT_NAME_DELIMITER"),
        help="Ophyd component delimiter (optional input) "
        "(default: from _OPHYD_CPT_NAME_DELIMITER env var)",
    )

    args = parser.parse_args()

    # -----------------------------------------------------------
    # Validation of: zmq_ip, zmq_port, nx_dir, log_dir
    # -----------------------------------------------------------

    if not args.zmq_ip:
        raise ValueError(
            "You must provide the ZeroMQ IP (--zmq-ip) or "
            "set the environment variable _ZMQ_IP."
        )

    if not args.zmq_port:
        raise ValueError(
            "You must provide the ZeroMQ port (--zmq-port) or "
            "set the environment variable _ZMQ_PORT."
        )

    if not args.nx_dir:
        raise ValueError(
            "You must provide a NeXus data directory (--nx-dir) or "
            "set _NX_FILE_DIR_PATH."
        )

    if not args.log_dir:
        raise ValueError(
            "You must provide a NeXus log directory (--log-dir) or "
            "set _NX_LOG_FILE_DIR_PATH."
        )

    # -----------------------------------------------------------
    # Logging configuration
    # -----------------------------------------------------------

    print(f"NeXus output directory: {args.nx_dir}")
    print(f"NeXus log directory:    {args.log_dir}")

    setup_nx_logger(
        console_level=LogLevel.ERROR,
        file_level=LogLevel.DEBUG,
        log_file_dir_path=args.log_dir,
        log_file_name="nx_log.log",
        log_format=None,  # default formatting
        max_file_size=10 * 1024 * 1024,  # 10 MB rotation
        backup_count=5,
        enable_console=True,
        enable_file=True,
    )

    # -----------------------------------------------------------
    # NexusWriter creation
    # -----------------------------------------------------------

    if args.cpt_delimiter:
        print(f"Using ophyd component delimiter: {args.cpt_delimiter}")
        nexus_writer = NexusWriter(
            nx_file_dir_path=args.nx_dir,
            cpt_name_delimiter=args.cpt_delimiter,
        )
    else:
        nexus_writer = NexusWriter(nx_file_dir_path=args.nx_dir)

    # -----------------------------------------------------------
    # RemoteDispatcher creation
    # -----------------------------------------------------------

    address = f"{args.zmq_ip}:{args.zmq_port}"
    print(f"ZMQ RemoteDispatcher connecting to {address}")

    remote_dispatcher = RemoteDispatcher(address)
    remote_dispatcher.subscribe(nexus_writer)

    print(
        "Subscription to 'nexus_writer' active. Ready to write NeXus files.\n"
        "Press Ctrl+C to exit safely."
    )

    # -----------------------------------------------------------
    # Event loop
    # -----------------------------------------------------------

    try:
        remote_dispatcher.start()
    except KeyboardInterrupt:
        print("Shutdown requested. Stopping dispatcher.")
        try:
            remote_dispatcher.stop()
        except Exception:
            pass
        print("Dispatcher stopped.")
