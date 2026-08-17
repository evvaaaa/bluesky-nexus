"""Kafka-based RemoteDispatcher service for Bluesky NeXus writing.

This module implements the Kafka backend for the ``bluesky_nexus_writer`` service.
It consumes Bluesky documents from a ZeroMQ publisher and forwards them to
:class:`NexusWriter`, which produces NeXus-compatible HDF5 files.
"""

from pathlib import Path

from bluesky_nexus import NexusHdfWriterCallback
from bluesky_nexus.logger import LOGGER


def run_kafka_dispatcher(
    root_output_directory: Path, kafka_brokers: str, kafka_group: str, kafka_topic: str
) -> None:
    """Start the Kafka-based Bluesky RemoteDispatcher.

    This method initializes a callback class with the selected output directory,
    and then subscribes to it over kafka.

    Parameters
    ----------
    root_output_directory : int
        The root directory that the nexus writer should write files to.
    kafka_brokers : str
        The kafka brokers to subscribe to, e.g `localhost:9092`.
    kafka_stream : str
        The kafka stream to subscribe to, "host1:9092,host2:9092".
    kafka_topic : str
        The kafka topic to subscribe to, e.g `bluesky.documents`.

    """
    try:
        from bluesky_kafka import RemoteDispatcher
    except Exception as exception:
        raise RuntimeError(
            "Could not import the kafka `RemoteDispatcher` from bluesky-kafka. "
            "Did you install `bluesky-nexus-callback[kafka]`?"
        ) from exception

    writer = NexusHdfWriterCallback(root_output_directory)

    # ---------------------------------------------------------------------------
    # Create and start the RemoteDispatcher
    # ---------------------------------------------------------------------------
    LOGGER.info(
        "Connecting to Kafka brokers '%s' on topic '%s' with group '%s'.",
        kafka_brokers,
        kafka_topic,
        kafka_group,
    )
    dispatcher = RemoteDispatcher(
        topics=[
            kafka_topic,
        ],
        bootstrap_servers=kafka_brokers,
        group_id=kafka_group,
    )
    dispatcher.subscribe(writer)
    LOGGER.info("Kafka RemoteDispatcher ready. Press Ctrl+C to stop.")

    try:
        dispatcher.start()
    except KeyboardInterrupt:
        LOGGER.warning("Shutdown requested by user (Ctrl+C).")
        try:
            dispatcher.stop()
        except Exception:
            LOGGER.exception("Error stopping Kafka dispatcher cleanly.")
        LOGGER.info("Kafka dispatcher stopped.")

    LOGGER.info("Kafka RemoteDispatcher ready. Press Ctrl+C to stop.")
