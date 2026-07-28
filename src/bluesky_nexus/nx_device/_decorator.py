"""A decorator for applying nexus schema to device."""

import copy
from pathlib import Path
from typing import Callable, Mapping, TypeVar

import yaml
from bluesky_nexus.schema import NxBase
from bluesky.protocols import HasHints

# from .model_schema.nx_models import validate_schema

T = TypeVar("T", bound=type)


def deep_update(dest: dict, src: Mapping) -> dict:
    """Recursively update `dest` with values from `src` (mutates dest)."""
    for k, v in src.items():
        if k in dest and isinstance(dest[k], dict) and isinstance(v, Mapping):
            deep_update(dest[k], v)
        else:
            dest[k] = copy.deepcopy(v)
    return dest


def _add_nx_schema_to_hints(device_cls: type[HasHints], schema: dict) -> None:
    original = device_cls.hints  # type: ignore

    @property
    def new_hints(self):
        hints = original.__get__(self).copy()
        hints["NX_class"] = schema.get("nx_class", hints.get("nx_class", "NX_object"))
        if "NX_schema" in hints:
            # Allows for inherited schema.
            deep_update(hints["NX_schema"], schema)
        else:
            hints["NX_schema"] = schema

        return hints

    device_cls.hints = new_hints  # type: ignore


class NexusDevice:
    """
    Decorator for adding nexus schema to the device.
    This can be done `from_path` or `from_dictionary` directly.
    """

    @classmethod
    def from_dictionary(cls, nx_schema: dict) -> Callable[[T], T]:
        NxBase.from_dict(nx_schema)  # Validates

        def decorator(device_cls: T) -> T:
            _add_nx_schema_to_hints(device_cls, nx_schema)
            return device_cls

        return decorator

    @classmethod
    def from_path(cls, path: str | Path) -> Callable[[T], T]:
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Path `{path}` does not exist.")
        with path.open("r") as f:
            nx_schema = yaml.safe_load(f)
        return cls.from_dictionary(nx_schema)
