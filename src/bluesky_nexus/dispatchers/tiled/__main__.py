"""Command-line interface for the ``bluesky_nexus`` hdf writer service over tiled."""

import argparse
from pathlib import Path

from bluesky_nexus.logger import LOGGER, setup_logging


def build_parser() -> argparse.ArgumentParser:
    """Define top-level arguments and the tiled subcommands."""
    parser = argparse.ArgumentParser(
        description="Bluesky NeXus writer tiled subscription service entry point."
    )

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
        "tiled_uri",
        type=str,
        help="URI of the tiled server to subscribe to.",
    )

    parser.add_argument(
        "tiled_secret",
        type=str,
        help="API key of the tiled server to subscribe to.",
    )

    return parser


def main() -> None:
    """Run the CLI entry point for ``python -m bluesky_nexus``."""

    parser = build_parser()
    args = parser.parse_args()

    try:
        from ._tiled import run_tiled_dispatcher
        from tiled.client import from_uri
    except Exception as exception:
        raise RuntimeError(
            "Could not import the zmq `HdfWriterSubscription` from bluesky-nexus. "
            "Did you install `bluesky-nexus[tiled]`?"
        ) from exception

    setup_logging(level=args.log_level)
    LOGGER.info(f"Connecting to tiled {args.tiled_uri}...")
    db = from_uri(uri=args.tiled_uri, api_key=args.tiled_secret)
    run_tiled_dispatcher(args.root_output_directory, db)


if __name__ == "__main__":
    main()
