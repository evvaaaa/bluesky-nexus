"""Command-line interface for the ``bluesky_nexus`` hdf writer service.

The CLI writes NeXus files from Bluesky documents using one of two backends:

    • ZeroMQ  (``zmq``)
    • Kafka   (``kafka``)

Both backends share the same logging system and accept environment variables
as fallbacks for most options.

See "bluesky_nexus --help", "bluesky_nexus kafka --help, and "bluesky_nexus zmq --help"
for more information on the arguments in specific modes...

===============================================================================
What this script does
===============================================================================

1. Parses global logging arguments.
2. Parses a backend selection: ``zmq`` or ``kafka``.
3. Sets up logging.
4. Starts the appropriate dispatcher and with the arguments.
"""

import argparse
import threading
from pathlib import Path

import uvicorn

from bluesky_nexus.dispatchers.kafka_dispatcher import run_kafka_dispatcher
from bluesky_nexus.dispatchers.zmq_dispatcher import run_zmq_dispatcher
from bluesky_nexus.logger import LOGGER, setup_logging

from .dispatchers.health import HealthManager

# TODO: Remove health.
DEFAULT_HEALTH_HOST = "127.0.0.1"
DEFAULT_HEALTH_PORT = 8080
DEFAULT_HEALTH_INTERVAL = 10.0


def validate_port(port: str | int) -> int:
    """Validate a TCP port number."""
    parsed_port = int(port)
    if parsed_port < 1 or parsed_port > 65535:
        raise argparse.ArgumentTypeError("Port must be in the range 1-65535.")
    return parsed_port


def validate_interval(interval: str) -> float:
    """Validate a positive health polling interval."""
    parsed_interval = float(interval)
    if parsed_interval <= 0:
        raise argparse.ArgumentTypeError("Health interval must be positive.")
    return parsed_interval


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

    # -----------------------------------------------------------------------
    # SUBPARSERS: zmq and kafka
    # -----------------------------------------------------------------------
    subparsers = parser.add_subparsers(
        title="Document source",
        dest="source",
        help="Choose the document source (zmq or kafka).",
    )

    # -----------------------------
    # ZMQ subcommand
    # -----------------------------

    zmq_parser = subparsers.add_parser(
        "zmq",
        help="Start a Bluesky ZMQ RemoteDispatcher.",
        description="Start a Bluesky RemoteDispatcher using ZeroMQ.",
    )

    zmq_parser.add_argument(
        "root_output_directory",
        type=Path,
        help="Root directory for NeXus files.",
    )

    zmq_parser.add_argument(
        "zmq_ip",
        type=str,
        help="ZeroMQ publisher IP.",
    )

    zmq_parser.add_argument(
        "zmq_port",
        type=validate_port,
        help="ZeroMQ publisher port.",
    )

    zmq_parser.add_argument(
        "--zmq-health-host",
        default=DEFAULT_HEALTH_HOST,
        help=("Host interface for the health endpoint."),
    )

    zmq_parser.add_argument(
        "--zmq-health-port",
        type=validate_port,
        default=DEFAULT_HEALTH_PORT,
        help="Port for the health endpoint.",
    )

    zmq_parser.add_argument(
        "--zmq-health-interval",
        type=validate_interval,
        default=DEFAULT_HEALTH_INTERVAL,
        help="Polling interval in seconds for the ZMQ reachability probe.",
    )

    # -----------------------------
    # Kafka subcommand
    # -----------------------------
    kafka_parser = subparsers.add_parser(
        "kafka",
        help="Start a Bluesky Kafka RemoteDispatcher.",
        description="Start a Bluesky RemoteDispatcher using Kafka.",
    )
    kafka_parser.add_argument(
        "root_output_directory",
        type=Path,
        help="Root directory for NeXus files.",
    )
    kafka_parser.add_argument(
        "kafka_brokers",
        type=str,
        help="Kafka bootstrap servers (e.g. 'host1:9092,host2:9092').",
    )

    kafka_parser.add_argument(
        "kafka_group",
        type=str,
        help="Kafka consumer group ID (e.g. nexus-writer).",
    )

    kafka_parser.add_argument(
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

    LOGGER.info("Starting dispatcher: '%s'", args.source)

    if args.source == "zmq":
        health_manager = HealthManager(
            zmq_host=args.zmq_health_host,
            zmq_port=args.zmq_health_port,
            interval=args.zmq_health_interval,
        )
        health_manager.start()

        def _run_health_api(manager: HealthManager, host: str, port: int) -> None:
            """Serve the FastAPI health endpoint."""
            uvicorn.run(manager.app, host=host, port=port, log_level="warning")

        thread = threading.Thread(
            target=_run_health_api,
            args=(health_manager, args.zmq_health_host, args.zmq_health_port),
            daemon=True,
        )
        thread.start()
        LOGGER.info(
            "Healthcheck endpoint listening on http://%s:%s/health.",
            args.zmq_health_host,
            args.zmq_health_port,
        )
        run_zmq_dispatcher(args.root_output_directory, args.zmq_ip, args.zmq_port)
    elif args.source == "kafka":
        # Kafka consumer groups usually have a default, often "default" or "group1".
        run_kafka_dispatcher(
            args.root_output_directory, args.kafka_brokers, args.kafka_group, args.kafka_topic
        )


if __name__ == "__main__":
    main()
