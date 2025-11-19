"""Entry point for the bluesky_nexus command-line interface.

This allows the user to start the RemoteDispatcher service via:

    python -m bluesky_nexus --zmq-ip 127.0.0.1 --zmq-port 5567

Arguments may be supplied via CLI flags or environment variables.
See `bluesky_nexus.services.remote_dispatcher_service` for full documentation.
"""

from bluesky_nexus.services.remote_dispatcher_service import run_dispatcher


def main():
    """Entry point for `python -m bluesky_nexus`.

    This function simply invokes the remote dispatcher service.
    """
    run_dispatcher()


if __name__ == "__main__":
    main()
