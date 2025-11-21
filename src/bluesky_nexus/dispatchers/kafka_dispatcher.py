"""Kafka-based RemoteDispatcher service for Bluesky NeXus writing.

This module implements the Kafka backend for the ``bluesky_nexus`` service.
It consumes Bluesky documents from an Apache Kafka topic and forwards them to
:class:`NexusWriter`, which produces NeXus-compatible HDF5 files.

Configuration may be provided through CLI arguments or environment variables.
CLI arguments take precedence over environment variables.

---------------------------------------------------------------------------
Required Configuration
---------------------------------------------------------------------------

| CLI Argument     | Environment Variable  | Description                       |
|------------------|-----------------------|-----------------------------------|
| --kafka-brokers  | _KAFKA_BROKERS        | Comma-separated Kafka servers     |
| --kafka-topic    | _KAFKA_TOPIC          | Kafka topic to subscribe to       |
| --nx-dir         | _NX_FILE_DIR_PATH     | Directory for NeXus output files  |

---------------------------------------------------------------------------
Optional Configuration
---------------------------------------------------------------------------

| CLI Argument     | Environment Variable          | Description                      |
|------------------|-------------------------------|----------------------------------|
| --kafka-group    | _KAFKA_GROUP                  | Kafka consumer group ID          |
| --cpt-delimiter  | _OPHYD_CPT_NAME_DELIMITER     | Custom ophyd component delimiter |

---------------------------------------------------------------------------
Runtime Behaviour
---------------------------------------------------------------------------

1. Resolve configuration via CLI or environment fallback.
2. Validate that all required values are present.
3. Validate the NeXus output directory.
4. Instantiate :class:`NexusWriter`.
5. Create a Kafka-backed :class:`RemoteDispatcher`.
6. Subscribe the writer to the dispatcher.
7. Consume Bluesky documents until interrupted.
8. Shut down the dispatcher cleanly.
"""

import os

from bluesky_kafka import RemoteDispatcher as KafkaDispatcher

from bluesky_nexus.callbacks.nexus_writer.writer_core import NexusWriter
from bluesky_nexus.common.logging_utils import logger
from bluesky_nexus.common.validation_utils import validate_directory


def run_kafka_dispatcher(args) -> None:
    """Start the Kafka-based Bluesky RemoteDispatcher.

    This function is invoked by the CLI entry point after argument parsing.
    It extracts the resolved configuration from ``args`` (with environment
    variable fallbacks handled at runtime), validates the required values,
    instantiates the :class:`NexusWriter`, and starts a Kafka-backed
    :class:`RemoteDispatcher`.

    All details about configuration, required arguments, environment
    variables, and runtime behaviour are documented in the module docstring.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments for the Kafka backend.

    Raises
    ------
    ValueError
        If one or more required configuration values (brokers, topic,
        or NeXus output directory) are missing.
    """
    # ---------------------------------------------------------------------------
    # Resolve configuration with fallback to environment variables if CLI absent
    # ---------------------------------------------------------------------------
    kafka_brokers = args.kafka_brokers or os.environ.get("_KAFKA_BROKERS")
    # Kafka consumer groups usually have a default, often "default" or "group1".
    kafka_group = args.kafka_group or os.environ.get("_KAFKA_GROUP", "default")
    kafka_topic = args.kafka_topic or os.environ.get("_KAFKA_TOPIC")
    nx_dir = args.nx_dir or os.environ.get("_NX_FILE_DIR_PATH")
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
            "Missing NeXus file output directory "
            "(--nx-dir or env. var. _NX_FILE_DIR_PATH)."
        )

    # ---------------------------------------------------------------------------
    # Validate NeXus file output directory
    # ---------------------------------------------------------------------------
    nx_path = validate_directory(nx_dir, "NeXus output directory")
    logger.info("Validated NeXus output directory: %s", nx_path)

    # ---------------------------------------------------------------------------
    # Initialize NexusWriter callback
    # ---------------------------------------------------------------------------
    if cpt_delimiter:
        logger.info("Using ophyd component delimiter: %s", cpt_delimiter)
        writer = NexusWriter(nx_file_dir_path=nx_path, cpt_name_delimiter=cpt_delimiter)
    else:
        writer = NexusWriter(nx_file_dir_path=nx_path)

    # ---------------------------------------------------------------------------
    # Create and start the Kafka dispatcher
    # ---------------------------------------------------------------------------
    logger.info(
        "Connecting to Kafka brokers '%s' on topic '%s' with group '%s'.",
        kafka_brokers,
        kafka_topic,
        kafka_group,
    )
    dispatcher = KafkaDispatcher(
        topics=[kafka_topic],
        bootstrap_servers=kafka_brokers,
        group_id=kafka_group,
    )
    dispatcher.subscribe(writer)
    logger.info("Kafka RemoteDispatcher ready. Press Ctrl+C to stop.")

    try:
        dispatcher.start()
    except KeyboardInterrupt:
        logger.warning("Shutdown requested by user (Ctrl+C).")
        try:
            dispatcher.stop()
        except Exception as e:
            logger.error("Error stopping Kafka dispatcher cleanly: %s", e)
        logger.info("Kafka dispatcher stopped.")
