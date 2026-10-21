"""Entrypoint for running NeXus hdf5 ".nxs" writer through zmq."""

from ._zmq import run_zmq_dispatcher

__all__ = ["run_zmq_dispatcher"]
