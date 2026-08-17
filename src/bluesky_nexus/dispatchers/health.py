"""Health monitoring utilities.

This module provides :class:`HealthManager` which exposes a FastAPI
``/health`` endpoint and runs periodic checks for ZMQ TCP reachability
and Tiled server availability via a provided ``connect_fn``.
"""

import socket
import threading

from fastapi import FastAPI

from bluesky_nexus.logger import LOGGER


class HealthManager:
    """Monitor ZMQ health and expose a `/health` endpoint.

    Args:
        zmq_host: Host for the ZMQ publisher TCP check.
        zmq_port: Port for the ZMQ publisher TCP check.
        interval: Polling interval in seconds for periodic checks.

    Attributes:
        app: FastAPI application exposing the `/health` route.
    """

    def __init__(self, zmq_host: str, zmq_port: int, interval: float = 10.0) -> None:
        """Initialize the HealthManager.

        ZMQ host/port are required and used to probe TCP reachability for
        the ZMQ publisher. The health endpoint always reports a composite
        status when ZMQ is configured.
        """
        self.zmq_host = zmq_host
        self.zmq_port = zmq_port
        self.interval = interval
        self._healthy: bool = True
        self._stop_event: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None
        self.app: FastAPI = FastAPI()
        self._register_routes()

    def _register_routes(self) -> None:
        @self.app.get("/health")
        def health() -> dict[str, str]:
            # If ZMQ monitoring is configured, require both to be healthy.
            if self.zmq_healthy:
                return {"status": "ok"}
            return {"zmq": "unhealthy"}

    def start(self) -> None:
        """Start the zmq health check service."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the zmq health check service."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            # ZMQ check
            try:
                with socket.create_connection((self.zmq_host, self.zmq_port), timeout=2):
                    if not self._healthy:
                        LOGGER.debug(
                            f"ZMQ TCP port {self.zmq_host}:{self.zmq_port} is "
                            "available. Marking as healthy."
                        )
                    self._healthy = True
            except Exception:
                if self._healthy:
                    LOGGER.debug(
                        f"ZMQ TCP port {self.zmq_host}:{self.zmq_port} is unavailable."
                        f" Marking as unhealthy."
                    )
                self._healthy = False
            self._stop_event.wait(self.interval)

    @property
    def zmq_healthy(self) -> bool:
        """Getter for healthy."""
        return self._healthy
