"""A decorator for applying nexus schema to device."""

import copy
import weakref
from pathlib import Path
from typing import Callable, TypeVar, cast

import yaml
from bluesky.protocols import HasHints

from bluesky_nexus.nx_schema.hint_structure import (
    PerObjectHintWithSchemaField,
)
from bluesky_nexus.nx_schema.nx_base import NxGroup

T = TypeVar("T")


def _deep_update(destination: dict, source: dict) -> None:
    """Recursively update `destination` with values from `source` (mutates destination)."""
    for source_key, source_value in source.items():
        if (
            (destination_value := destination.get(source_key))
            and isinstance(destination_value, dict)
            and isinstance(source_key, dict)
        ):
            if (
                destination_value["nx_class"] == "NXfield"
                or source_value["nx_class"] == "NXfield"
            ):
                destination[source_key] = source_value
            else:
                _deep_update(destination_value, source_value)
        else:
            destination[source_key] = source_value


_schema_added: weakref.WeakKeyDictionary[type[HasHints], dict] = (
    weakref.WeakKeyDictionary()
)
"""Used to cache added schema. This allows multi-inheritence."""
_inheritance_structure: weakref.WeakKeyDictionary[type[HasHints], bool] = (
    weakref.WeakKeyDictionary()
)


def _parse_parents_schema(instance: HasHints, cls: type[HasHints], sofar: dict):
    for direct_parent in reversed(cls.__bases__):
        if _inheritance_structure.get(direct_parent):
            _parse_parents_schema(instance, direct_parent, sofar)
        if direct_parent in _schema_added:
            _deep_update(sofar, _schema_added[direct_parent])


def _add_nx_schema_and_device_metadata_to_hints(
    device_cls: type[HasHints], schema: dict, inherit: bool
) -> None:
    original = device_cls.hints  # type: ignore
    _schema_added[device_cls] = schema
    _inheritance_structure[device_cls] = inherit

    @property  # type: ignore
    def new_hints(self: HasHints) -> PerObjectHintWithSchemaField:
        hints = original.__get__(self).copy()

        if inherit:
            nx_schema: dict = {}
            _parse_parents_schema(self, type(self), nx_schema)
            _deep_update(nx_schema, schema)

        else:
            nx_schema = schema

        hints = copy.deepcopy(original.__get__(self))
        hints["NX_schema"] = nx_schema
        hints["NX_class"] = nx_schema["nx_class"]

        if hasattr(self, "md"):
            hints["metadata"] = self.md  # type: ignore

        return hints

    device_cls.hints = new_hints  # type: ignore


class NexusDevice:
    """
    Decorator for adding nexus schema to the device.
    This can be done `from_path` or `from_dictionary` directly.
    """

    @classmethod
    def from_dictionary(
        cls, nx_schema: dict, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen nx_schema dictionary into the hints of the decorated device.

        If `inherit` then parent device schema will be included.
        """
        validated_and_substituted = NxGroup.from_dict(nx_schema).model_dump()

        def decorator(device_cls: type[T]) -> type[T]:
            if not isinstance(device_cls, HasHints):
                raise TypeError(
                    f"Cannot apply nexus schema to {device_cls} as it "
                    "is not `HasHints`."
                )
            _add_nx_schema_and_device_metadata_to_hints(
                cast(type[HasHints], device_cls), validated_and_substituted, inherit
            )
            return device_cls

        return decorator

    @classmethod
    def from_path(
        cls, path: str | Path, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen nx_schema path into the hints of the decorated device.

        If `inherit` then parent device schema will be included.
        """
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Path `{path}` does not exist.")
        with path.open("r") as f:
            nx_schema = yaml.safe_load(f)
        return cls.from_dictionary(nx_schema, inherit=inherit)
