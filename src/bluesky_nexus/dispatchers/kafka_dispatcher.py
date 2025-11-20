"""Kafka-based RemoteDispatcher service for Bluesky NeXus writing.

This module implements a service entry point that consumes Bluesky documents
from an Apache Kafka topic and forwards them to the :class:`NexusWriter`
callback, which generates NeXus-compliant HDF5 files.

The dispatcher configuration may be provided either via CLI arguments or via
environment variables. CLI arguments take precedence, while environment
variables provide optional fallback values.

### Required Configuration

| CLI Argument     | Environment Variable  | Description                               |
|------------------|-----------------------|-------------------------------------------|
| --kafka-brokers  | _KAFKA_BROKERS        | Kafka bootstrap server list               |
| --kafka-topic    | _                     | Kafka topic to subscribe to (no fallback) |
| --nx-dir         | _NX_FILE_DIR_PATH     | Output dir for generated NeXus files      |
| --log-dir        | _NX_LOG_FILE_DIR_PATH | Output dir for NexusWriter log files      |

### Optional Configuration

| CLI Argument    | Environment Variable              | Description                 |
|-----------------|-----------------------------------|-----------------------------|
| --kafka-group   | _KAFKA_GROUP (default: "default") | Kafka consumer group        |
| --cpt-delimiter | _OPHYD_CPT_NAME_DELIMITER         | Custom ophyd cpt name delim |

### Runtime Behaviour

1. Validates that all required inputs are available.
2. Initializes logging via ``setup_nx_logger`` so that the NexusWriter uses both
   file and console logging.
3. Instantiates a :class:`NexusWriter` with optional component delimiter.
4. Creates a :class:`KafkaDispatcher` listening to the given Kafka topic.
5. Subscribes the NexusWriter to the dispatcher and starts consuming documents.
6. Gracefully stops on Ctrl+C.

This module is designed to be called by a CLI wrapper that assembles the
argument namespace before invoking :func:`run_kafka_dispatcher`.
"""

import os

from bluesky_kafka import RemoteDispatcher as KafkaDispatcher

from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import LogLevel, setup_nx_logger


def run_kafka_dispatcher(args) -> None:
    """Start a Bluesky RemoteDispatcher using Kafka.

    This function is executed when the user selects the ``kafka`` data-source
    from the top-level CLI (``python -m bluesky_nexus --source kafka``).

    It performs the following responsibilities:

    1. Resolve configuration values from CLI arguments, with optional
       fallbacks to environment variables.
    2. Validate all required parameters.
    3. Initialize logging for the NexusWriter (console + rotating file logs).
    4. Instantiate the `NexusWriter` callback.
    5. Instantiate and start a Kafka-backed `RemoteDispatcher`, subscribing
       the NexusWriter to Bluesky documents on the configured topic.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments for the Kafka subparser. Expected attributes:

        Required:
            - kafka_brokers : str
                Comma-separated Kafka bootstrap servers.
            - kafka_topic : str
                Name of the Kafka topic to subscribe to.
            - nx_dir : str
                Directory where NeXus files will be written.
            - log_dir : str
                Directory where NeXus log files will be stored.

        Optional:
            - kafka_group : str, default="default"
                Kafka consumer group to join.
            - cpt_delimiter : str or None
                Custom ophyd component name delimiter.

    Environment Variable Fallbacks
    ------------------------------
    CLI arguments take precedence. If not provided, the following environment
    variables supply fallback values:

        _KAFKA_BROKERS              → --kafka-brokers
        _KAFKA_GROUP                → --kafka-group
        _KAFKA_TOPIC                → --kafka-topic
        _NX_FILE_DIR_PATH           → --nx-dir
        _NX_LOG_FILE_DIR_PATH       → --log-dir
        _OPHYD_CPT_NAME_DELIMITER   → --cpt-delimiter

    Raises
    ------
    ValueError
        If any required configuration value is missing.

    Notes
    -----
    - The dispatcher runs until interrupted (Ctrl+C).
    - On shutdown, it attempts a clean dispatcher termination.
    """
    # ---------------------------------------------------------------------------
    # Resolve configuration with fallback to environment variables if CLI absent
    # ---------------------------------------------------------------------------
    kafka_brokers = args.kafka_brokers or os.environ.get("_KAFKA_BROKERS")
    # Kafka consumer groups usually have a default, often "default" or "group1".
    kafka_group = args.kafka_group or os.environ.get("_KAFKA_GROUP", "default")
    kafka_topic = args.kafka_topic or os.environ.get("_KAFKA_TOPIC")
    nx_dir = args.nx_dir or os.environ.get("_NX_FILE_DIR_PATH")
    log_dir = args.log_dir or os.environ.get("_NX_LOG_FILE_DIR_PATH")
    cpt_delimiter = args.cpt_delimiter or os.environ.get("_OPHYD_CPT_NAME_DELIMITER")

    # ---------------------------------------------------------------------------
    # Validation of required inputs
    # ---------------------------------------------------------------------------
    if not kafka_brokers:
        raise ValueError(
            "Missing Kafka brokers (--kafka-brokers or env. var. _KAFKA_BROKERS)."
        )

    if not kafka_topic:
        raise ValueError("Missing Kafka topic (--kafka-topic).")

    if not nx_dir:
        raise ValueError(
            "Missing NeXus output directory (--nx-dir or env. var.  _NX_FILE_DIR_PATH)."
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
    # Create and start the Kafka dispatcher
    # ---------------------------------------------------------------------------
    print(
        f"Connecting to Kafka brokers '{kafka_brokers}' "
        f"on topic '{kafka_topic}' with group '{kafka_group}'."
    )
    dispatcher = KafkaDispatcher(
        topics=[kafka_topic],
        bootstrap_servers=kafka_brokers,
        group_id=kafka_group,
    )
    dispatcher.subscribe(writer)
    print("Kafka RemoteDispatcher ready. Press Ctrl+C to stop.")

    try:
        dispatcher.start()
    except KeyboardInterrupt:
        print("Shutdown requested.")
        try:
            dispatcher.stop()
        except Exception:
            pass
        print("Kafka dispatcher stopped.")
