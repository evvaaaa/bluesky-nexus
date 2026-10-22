"""Entrypoint for tiled dispatcher."""

try:
    from ._tiled import run_tiled_dispatcher

    __all__ = ["run_tiled_dispatcher"]
except ImportError:
    # In the event tiled wasn't installed as an optional dependency.
    pass
