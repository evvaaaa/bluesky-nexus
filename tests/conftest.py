import logging
import time
from collections.abc import Iterator
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as MultiprocessingQueue
from pathlib import Path, PurePath

import pytest
import zmq
from bluesky import RunEngine
from bluesky.callbacks.zmq import Proxy, Publisher

from bluesky_nexus import NexusCallback, NexusHdfWriter
from bluesky_nexus.dispatchers import run_zmq_dispatcher
from bluesky_nexus.logger import setup_logging
from bluesky_nexus.nx_device._decorator import _inheritance_structure, _schema_added
from bluesky_nexus.nx_schema import NX_CLASS_TO_BASEMODEL


@pytest.fixture()
def tmpdir(tmpdir: PurePath):
    """Quick patch to get the full Path object from the PurePath."""
    return Path(tmpdir)


@pytest.fixture(scope="session", autouse=True)
def logs_on_during_tests():
    """Set up default logging across all tests."""
    setup_logging()


@pytest.fixture(scope="function", autouse=True)
def ensure_fresh_mutable_global_caches(monkeypatch):
    """It's important that any tests adding basemodels, or adding schema to
    classes don't modify the environment.
    """
    monkeypatch.setattr(
        "bluesky_nexus.nx_device._decorator._schema_added",
        _schema_added.copy(),
    )
    monkeypatch.setattr(
        "bluesky_nexus.nx_device._decorator._inheritance_structure",
        _inheritance_structure.copy(),
    )
    monkeypatch.setattr(
        "bluesky_nexus.nx_schema.nx_base.NX_CLASS_TO_BASEMODEL",
        NX_CLASS_TO_BASEMODEL.copy(),
    )


@pytest.fixture()
def RE_directly_subscribed(tmpdir: Path):
    RE = RunEngine()
    RE.subscribe(NexusCallback(NexusHdfWriter(tmpdir)))
    return RE


@pytest.fixture(scope="function")
def zmq_proxy_subprocess() -> Iterator[Process]:
    exception_queue: MultiprocessingQueue[Exception] = Queue()

    def start_proxy_and_dispatcher() -> None:
        try:
            proxy = Proxy(in_address="127.0.0.1:5577", out_address="127.0.01:5578")
            proxy.start()
        except Exception as e:
            exception_queue.put(e)

    zmq_proxy = Process(target=start_proxy_and_dispatcher, daemon=True)
    try:
        zmq_proxy.start()
        time.sleep(0.1)  # Enough time for process start.
        yield zmq_proxy
    finally:
        if not zmq_proxy.is_alive():
            if not exception_queue.empty():
                raise exception_queue.get()
            else:
                raise RuntimeError("ZMQ proxy died during test.")
        zmq_proxy.terminate()
        zmq_proxy.join(timeout=1)
        zmq_proxy.close()


def _start_zmq_dispatcher(
    tmpdir: Path, exception_queue: MultiprocessingQueue, log_path: Path
) -> None:
    try:
        from bluesky_nexus.logger import LOGGER, setup_logging

        setup_logging()
        file_handler = logging.FileHandler(
            log_path,
            mode="a",
            encoding="utf-8",
        )
        LOGGER.addHandler(file_handler)
        run_zmq_dispatcher(tmpdir, zmq_ip="127.0.0.1", zmq_port=5578)

    except Exception as e:
        exception_queue.put(e)


@pytest.fixture(scope="function")
def zmq_callback_process(
    tmpdir: Path, zmq_proxy_subprocess: Process, caplog: pytest.LogCaptureFixture
) -> Iterator[Process]:
    exception_queue: MultiprocessingQueue[Exception] = Queue()
    zmq_callback = Process(
        target=_start_zmq_dispatcher, args=(tmpdir, exception_queue, tmpdir / "test-log.log")
    )
    try:
        zmq_callback.start()
        time.sleep(0.1)  # Enough time for the process to start.
        yield zmq_callback
    finally:

        def wait_for_zmq_drain(out_address: str, timeout: float = 2.0) -> None:
            ctx = zmq.Context()
            socket = ctx.socket(zmq.SUB)
            socket.connect(out_address)
            socket.setsockopt(zmq.SUBSCRIBE, b"")
            poller = zmq.Poller()
            poller.register(socket, zmq.POLLIN)
            last_msg_time = time.time()
            while True:
                socks = dict(poller.poll(timeout=100))
                if socket in socks and socks[socket] == zmq.POLLIN:
                    _ = socket.recv()
                    last_msg_time = time.time()
                elif time.time() - last_msg_time > timeout:
                    break
            socket.close()
            ctx.term()

        wait_for_zmq_drain("tcp://127.0.0.1:5578")
        if not zmq_callback.is_alive():
            if not exception_queue.empty():
                raise exception_queue.get()
            else:
                raise RuntimeError("ZMQ Plot callback died during test.")

        join_time = 1
        zmq_callback.terminate()
        zmq_callback.join(timeout=join_time)
        zmq_callback.close()


@pytest.fixture(scope="function")
def RE_subscribed_over_zmq(zmq_callback_process: Process) -> Iterator[RunEngine]:
    RE = RunEngine()
    publisher = Publisher(address="127.0.0.1:5577")
    RE.subscribe(publisher)
    try:
        yield RE
    finally:
        publisher.close()
