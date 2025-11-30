"""Command-line interface for the ``bluesky_nexus`` writer service.

The CLI writes NeXus files from Bluesky documents using one of two backends:

    • ZeroMQ  (``zmq``)
    • Kafka   (``kafka``)

Both backends share the same logging system and accept environment variables
as fallbacks for most options. If no log directory is provided (and no
``_NX_LOG_FILE_DIR_PATH`` environment variable is set), file logging is
disabled and only console logging is used (if enabled).

===============================================================================
Quick Start
===============================================================================

Run the ZMQ backend:

python -m bluesky_nexus \
    --log-dir /home/user/nexus_logs \
    zmq \
        --zmq-ip localhost \
        --zmq-port 5578 \
        --nx-dir /home/user/nexus_output


Run the Kafka backend:

python -m bluesky_nexus \
    --log-dir /home/user/nexus_logs \
    kafka \
        --kafka-brokers localhost:9092 \
        --kafka-topic bluesky.documents \
        --nx-dir /home/user/nexus_output

===============================================================================
Viewing Help
===============================================================================

Global help (logging options + subcommands):

    python -m bluesky_nexus --help

Help for the ZMQ backend:

    python -m bluesky_nexus zmq --help

Help for the Kafka backend:

    python -m bluesky_nexus kafka --help


===============================================================================
Backend-Specific Required Arguments
===============================================================================

ZMQ backend requires:
    --zmq-ip and --zmq-port
    or environment variables:
    _ZMQ_IP and _ZMQ_PORT

Kafka backend requires:
    --kafka-brokers and --kafka-topic
    or environment variables:
    _KAFKA_BROKERS and _KAFKA_TOPIC

All other backend options are optional and may fall back to environment variables.

===============================================================================
Top-Level Logging Options (must come BEFORE ``zmq``/``kafka``)
===============================================================================

| CLI Argument    | Env Variable           | Description                               |
|-----------------|------------------------|-------------------------------------------|
| --log-dir       | _NX_LOG_FILE_DIR_PATH  | Directory for log files (optional)        |
| --console-level | _NX_CONSOLE_LOG_LEVEL  | Console log level (default=ERROR)         |
| --file-level    | _NX_FILE_LOG_LEVEL     | File log level (default=DEBUG)            |
| --log-file-name | _NX_LOG_FILE_NAME      | Log filename (default=nx_log.log)         |
| --file-max-size | _NX_LOG_FILE_MAX_SIZE  | Rotate logs above this size (default=10MB)|
| --backup-count  | _NX_BACKUP_COUNT       | Num of rotated logs to keep (default=5)   |
| --enable-console| _NX_ENABLE_CONSOLE_LOG | Enable console logging (default=True)     |

⚠️ All logging arguments must appear *before* the backend (``zmq`` or ``kafka``).


===============================================================================
ZMQ Backend Options (after ``zmq``)
===============================================================================

| CLI Argument     | Env Variable             | Description                        |
|------------------|---------------------------|-----------------------------------|
| --zmq-ip         | _ZMQ_IP                   | IP of the Bluesky ZMQ publisher   |
| --zmq-port       | _ZMQ_PORT                 | Port of the Bluesky ZMQ publisher |
| --nx-dir         | _NX_FILE_DIR_PATH         | Output directory for NeXus files  |
| --cpt-delimiter  | _OPHYD_CPT_NAME_DELIMITER | Ophyd component name delimiter    |


===============================================================================
Kafka Backend Options (after ``kafka``)
===============================================================================

| CLI Argument     | Env Variable             | Description                         |
|------------------|---------------------------|------------------------------------|
| --kafka-brokers  | _KAFKA_BROKERS            | Comma-separated Kafka servers      |
| --kafka-group    | _KAFKA_GROUP              | Kafka consumer group               |
| --kafka-topic    | _KAFKA_TOPIC              | Topic containing Bluesky documents |
| --nx-dir         | _NX_FILE_DIR_PATH         | Output directory for NeXus files   |
| --cpt-delimiter  | _OPHYD_CPT_NAME_DELIMITER | Ophyd component name delimiter     |


===============================================================================
What this script does
===============================================================================

1. Parses global logging arguments.
2. Parses a backend selection: ``zmq`` or ``kafka``.
3. Sets up logging exactly once.
4. Starts the appropriate dispatcher and passes documents to the writer.
"""

import argparse
import os

from bluesky_nexus.common.logging_utils import LogLevel, logger, setup_nx_logger
from bluesky_nexus.common.validation_utils import validate_directory
from bluesky_nexus.dispatchers.kafka_dispatcher import run_kafka_dispatcher
from bluesky_nexus.dispatchers.zmq_dispatcher import run_zmq_dispatcher


# ---------------------------------------------------------------------------
# Top-level parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Define top-level arguments and the zmq/kafka subcommands."""
    parser = argparse.ArgumentParser(
        description="Bluesky NeXus writer service entry point."
    )

    # -----------------------------------------------------------------------
    # TOP-LEVEL LOGGING ARGUMENTS
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--log-dir",
        required=False,
        help="Directory for NeXus logs (env: _NX_LOG_FILE_DIR_PATH). Logging to file"
        " is disabled if --log-dir or env: _NX_LOG_FILE_DIR_PATH is not defined",
    )

    parser.add_argument(
        "--console-level",
        required=False,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console log level (env: _NX_CONSOLE_LOG_LEVEL).",
    )

    parser.add_argument(
        "--file-level",
        required=False,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="File log level (env: _NX_FILE_LOG_LEVEL).",
    )

    parser.add_argument(
        "--log-file-name",
        required=False,
        type=str,
        help="Log file name (env: _NX_LOG_FILE_NAME). Default: nx_log.log",
    )

    parser.add_argument(
        "--file-max-size",
        required=False,
        type=int,
        help="Maximum file size before rotation (env: _NX_LOG_FILE_MAX_SIZE).",
    )

    parser.add_argument(
        "--backup-count",
        required=False,
        type=int,
        help="Number of rotated log files to keep (env: _NX_BACKUP_COUNT).",
    )

    parser.add_argument(
        "--enable-console",
        required=False,
        type=str,
        choices=["True", "False"],
        help="Enable console logging (env: _NX_ENABLE_CONSOLE_LOG). Default: True",
    )

    # -----------------------------------------------------------------------
    # SUBPARSERS: zmq and kafka
    # -----------------------------------------------------------------------
    subparsers = parser.add_subparsers(
        title="Document source",
        dest="source",
        required=True,
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
        "--zmq-ip",
        required=False,
        help="ZeroMQ publisher IP (env: ``_ZMQ_IP``).",
    )

    zmq_parser.add_argument(
        "--zmq-port",
        required=False,
        help="ZeroMQ publisher port (env: ``_ZMQ_PORT``).",
    )

    zmq_parser.add_argument(
        "--nx-dir",
        required=False,
        help="Directory for NeXus files (env: ``_NX_FILE_DIR_PATH``).",
    )

    zmq_parser.add_argument(
        "--cpt-delimiter",
        required=False,
        help="Delimiter for ophyd component names "
        "(env: ``_OPHYD_CPT_NAME_DELIMITER``).",
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
        required=False,
        help="Kafka topic to subscribe to (e.g. bluesky.documents)",
    )

    kafka_parser.add_argument(
        "--nx-dir",
        required=False,
        help="Directory for NeXus files (env: ``_NX_FILE_DIR_PATH``).",
    )

    kafka_parser.add_argument(
        "--cpt-delimiter",
        required=False,
        help="Delimiter for ophyd component names "
        "(env: ``_OPHYD_CPT_NAME_DELIMITER``).",
    )
    return parser


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------
def main():
    """Run the CLI entry point for ``python -m bluesky_nexus``."""
    parser = build_parser()
    args = parser.parse_args()

    # -------------------------------------------------------
    # Resolve logging configuration with env fallbacks
    # -------------------------------------------------------

    log_dir = args.log_dir or os.environ.get("_NX_LOG_FILE_DIR_PATH", None)

    log_file_name = args.log_file_name or os.environ.get(
        "_NX_LOG_FILE_NAME", "nx_log.log"
    )

    log_file_max_size = args.file_max_size or int(
        os.environ.get("_NX_LOG_FILE_MAX_SIZE", 10 * 1024 * 1024)
    )

    backup_count = args.backup_count or int(os.environ.get("_NX_BACKUP_COUNT", 5))

    console_level_str = (
        args.console_level or os.environ.get("_NX_CONSOLE_LOG_LEVEL", "ERROR")
    ).upper()

    file_level_str = (
        args.file_level or os.environ.get("_NX_FILE_LOG_LEVEL", "DEBUG")
    ).upper()

    # Validate levels to avoid KeyError
    try:
        console_level = LogLevel[console_level_str]
    except KeyError:
        raise ValueError(f"Invalid console log level: {console_level_str}") from None

    try:
        file_level = LogLevel[file_level_str]
    except KeyError:
        raise ValueError(f"Invalid file log level: {file_level_str}") from None

    enable_console = _str_to_bool(
        args.enable_console or os.environ.get("_NX_ENABLE_CONSOLE_LOG", "True")
    )

    # -------------------------------------------------------
    # Validate log directory
    # -------------------------------------------------------
    log_path = None
    if log_dir is not None:
        log_path = validate_directory(log_dir, "Log directory")
        logger.info("Logging directory %s validated.", log_path)
    else:
        logger.info("Logging directory not defined. Logging to file disabled.")

    # -------------------------------------------------------
    # Configure logging
    # -------------------------------------------------------
    setup_nx_logger(
        console_level=console_level,
        file_level=file_level,
        log_file_dir_path=log_path,
        log_file_name=log_file_name,
        log_file_max_size=log_file_max_size,
        backup_count=backup_count,
        enable_console=enable_console,
    )

    logger.info("Starting dispatcher: '%s'", args.source)

    # -------------------------------------------------------
    # Dispatch to backend
    # -------------------------------------------------------
    if args.source == "zmq":
        run_zmq_dispatcher(args)
    elif args.source == "kafka":
        run_kafka_dispatcher(args)
    else:
        raise ValueError(f"Unknown dispatcher source: {args.source!r}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _str_to_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    main()
