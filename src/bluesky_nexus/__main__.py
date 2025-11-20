"""Entry point for the ``bluesky_nexus`` command-line interface.

Usage:
    bluesky_nexus zmq   --zmq-ip 127.0.0.1 --zmq-port 5567
    bluesky_nexus kafka --kafka-brokers localhost:9092 --kafka-group nexus-writer

Each subcommand initializes the appropriate document source
(ZMQ or Kafka), configures a RemoteDispatcher, and attaches
the NexusWriter callback.
"""

import argparse

from bluesky_nexus.dispatchers.kafka_dispatcher import run_kafka_dispatcher
from bluesky_nexus.dispatchers.zmq_dispatcher import run_zmq_dispatcher


def build_parser() -> argparse.ArgumentParser:
    """Define subcommands: ``zmq`` and ``kafka`` for selecting the document source.

    These determine the document transport to be used by the RemoteDispatcher.
    Each subcommand provides its own broker- specific arguments while
    sharing common configuration options for the NexusWriter, such as
    directory paths and the ophyd component name delimiter.

    Returns
    -------
    argparse.ArgumentParser
        A fully configured argument parser ready to parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        description="Bluesky NeXus writer service entry point."
    )

    subparsers = parser.add_subparsers(
        title="Document source",
        dest="source",
        required=True,
        help="Choose the document source (zmq or kafka).",
    )

    # -------------------------------------------------------
    # ZMQ SUBPARSER
    # -------------------------------------------------------
    zmq_parser = subparsers.add_parser(
        "zmq",
        help="Start a Bluesky ZMQ RemoteDispatcher.",
        description="Start a Bluesky RemoteDispatcher using ZeroMQ.",
    )

    zmq_parser.add_argument(
        "--zmq-ip", required=False, help="ZeroMQ publisher IP (env: ``_ZMQ_IP``)."
    )

    zmq_parser.add_argument(
        "--zmq-port", required=False, help="ZeroMQ publisher port (env: ``_ZMQ_PORT``)."
    )

    zmq_parser.add_argument(
        "--nx-dir",
        required=False,
        help="Directory for NeXus files (env: ``_NX_FILE_DIR_PATH``).",
    )

    zmq_parser.add_argument(
        "--log-dir",
        required=False,
        help="Directory for NeXus logs (env: ``_NX_LOG_FILE_DIR_PATH``).",
    )

    zmq_parser.add_argument(
        "--cpt-delimiter",
        required=False,
        help="Delimiter for ophyd component names "
        "(env: ``_OPHYD_CPT_NAME_DELIMITER``).",
    )

    # -------------------------------------------------------
    # KAFKA SUBPARSER
    # -------------------------------------------------------
    kafka_parser = subparsers.add_parser(
        "kafka",
        help="Start a Bluesky Kafka RemoteDispatcher.",
        description="Start a Bluesky RemoteDispatcher using Kafka.",
    )

    kafka_parser.add_argument(
        "--kafka-brokers",
        required=False,
        help="Kafka bootstrap servers (e.g. 'host1:9092,host2:9092').",
    )

    kafka_parser.add_argument(
        "--kafka-group",
        required=False,
        help="Kafka consumer group ID (e.g. nexus-writer).",
    )

    kafka_parser.add_argument(
        "--kafka-topic",
        required=True,
        help="Kafka topic to subscribe to (e.g. bluesky.documents)",
    )

    kafka_parser.add_argument(
        "--nx-dir",
        required=False,
        help="Directory for NeXus files (env: ``_NX_FILE_DIR_PATH``).",
    )

    kafka_parser.add_argument(
        "--log-dir",
        required=False,
        help="Directory for NeXus logs (env: ``_NX_LOG_FILE_DIR_PATH``).",
    )

    kafka_parser.add_argument(
        "--cpt-delimiter",
        required=False,
        help="Delimiter for ophyd component names "
        "(env: ``_OPHYD_CPT_NAME_DELIMITER``).",
    )

    return parser


def main():
    """Run the CLI entry point for ``python -m bluesky_nexus``.

    This function builds the CLI parser, parses command-line
    arguments, and dispatches control to the appropriate backend
    (ZMQ or Kafka) to initialize and start the corresponding
    RemoteDispatcher service.

    Raises
    ------
    ValueError
        If the selected ``--source`` is not recognized.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.source == "zmq":
        run_zmq_dispatcher(args)

    elif args.source == "kafka":
        run_kafka_dispatcher(args)

    else:
        raise ValueError(f"Unknown dispatcher source: {args.source!r}")


if __name__ == "__main__":
    main()
