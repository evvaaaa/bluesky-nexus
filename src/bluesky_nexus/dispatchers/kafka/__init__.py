"""Entrypoint for running NeXus hdf5 ".nxs" writer through kafka."""

from ._kafka import run_kafka_dispatcher

__all__ = ["run_kafka_dispatcher"]
