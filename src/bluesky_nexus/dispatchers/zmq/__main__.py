"""Command-line interface for the ``bluesky_nexus`` hdf writer service over zmq."""

import argparse
import threading
from pathlib import Path

import uvicorn

from bluesky_nexus.logger import LOGGER, setup_logging

from ._zmq import run_zmq_dispatcher


def validate_port(port: str | int) -> int:
    """Validate a TCP port number."""
    parsed_port = int(port)
    if parsed_port < 1 or parsed_port > 65535:
        raise argparse.ArgumentTypeError("Port must be in the range 1-65535.")
    return parsed_port


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Define top-level arguments and the zmq/kafka subcommands."""
    parser = argparse.ArgumentParser(description="Bluesky NeXus writer service entry point.")

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console log level.",
    )

    parser.add_argument(
        "root_output_directory",
        type=Path,
        help="Root directory for NeXus files.",
    )

    parser.add_argument(
        "zmq_ip",
        type=str,
        help="ZeroMQ publisher IP.",
    )

    parser.add_argument(
        "zmq_port",
        type=validate_port,
        help="ZeroMQ publisher port.",
    )
    return parser


def main() -> None:
    """Run the CLI entry point for ``python -m bluesky_nexus``."""
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(level=args.log_level)
    LOGGER.info("Starting zmq dispatcher.")
    run_zmq_dispatcher(args.root_output_directory, args.zmq_ip, args.zmq_port)


if __name__ == "__main__":
    main()
