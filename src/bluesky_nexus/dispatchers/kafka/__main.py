"""Command-line interface for the ``bluesky_nexus`` hdf writer service over kafka."""

import argparse
from pathlib import Path

from bluesky_nexus.logger import LOGGER, setup_logging

from ._kafka import run_kafka_dispatcher


def build_parser() -> argparse.ArgumentParser:
    """Define top-level arguments and the zmq/kafka subcommands."""
    parser = argparse.ArgumentParser(description="Bluesky NeXus writer kafka service entry point.")

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
        "kafka_brokers",
        type=str,
        help="Kafka bootstrap servers (e.g. 'host1:9092,host2:9092').",
    )

    parser.add_argument(
        "kafka_group",
        type=str,
        help="Kafka consumer group ID (e.g. nexus-writer).",
    )

    parser.add_argument(
        "kafka_topic",
        type=str,
        help="Kafka topic to subscribe to (e.g. bluesky.documents)",
    )

    return parser


def main() -> None:
    """Run the CLI entry point for ``python -m bluesky_nexus``."""
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(level=args.log_level)
    LOGGER.info("Starting kafka dispatcher.")
    # Kafka consumer groups usually have a default, often "default" or "group1".
    run_kafka_dispatcher(
        args.root_output_directory, args.kafka_brokers, args.kafka_group, args.kafka_topic
    )


if __name__ == "__main__":
    main()
