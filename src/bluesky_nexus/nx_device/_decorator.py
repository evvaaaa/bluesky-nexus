"""A decorator for applying nexus schema to device."""

import copy
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import yaml
from bluesky.protocols import HasHints

from bluesky_nexus.nx_schema.hint_structure import (
    PerObjectHintWithSchemaField,
)
from bluesky_nexus.nx_schema.nx_base import NxGroup

T = TypeVar("T")


def _deep_update_raw_schema(destination: dict, source: dict, prefer_source) -> None:
    """
    Recursively update `destination` with values from `source,`
    mutating the destination.
    """
    for source_key, source_value in source.items():
        destination_value = destination.get(source_key)
        if isinstance(source_value, dict) and isinstance(destination_value, dict):
            if (source_value.get("nx_class") == "NXfield") ^ (
                destination_value.get("nx_class") == "NXfield"
            ):
                if prefer_source:
                    destination[source_key] = source_value
            else:
                _deep_update_raw_schema(destination_value, source_value, prefer_source)
        elif (not prefer_source and destination_value is None) or prefer_source:
            destination[source_key] = source_value


_schema_added: weakref.WeakKeyDictionary[type[HasHints], dict] = (
    weakref.WeakKeyDictionary()
)
_inheritance_structure: weakref.WeakKeyDictionary[type[HasHints], bool] = (
    weakref.WeakKeyDictionary()
)


def _parse_parents_schema(cls: type[T], sofar: dict):
    for direct_parent in reversed(cls.__bases__):
        # If inherit=False don't look through the parents.
        # If the below is None then the wrapper wasn't called
        # on that parent class, but may have been on one of it's parents.
        if _inheritance_structure.get(direct_parent) is not False:
            _parse_parents_schema(direct_parent, sofar)

        if schema_added := _schema_added.get(direct_parent):
            _deep_update_raw_schema(sofar, schema_added, True)


def _add_inherited_schema(device_cls: type[HasHints], schema: dict):
    schema_with_parents: dict = {}
    _parse_parents_schema(device_cls, schema_with_parents)
    _deep_update_raw_schema(schema, schema_with_parents, False)


def _add_nx_schema_and_device_metadata_to_hints(
    device_cls: type[T], schema: dict
) -> None:
    original = device_cls.hints  # type: ignore

    @property  # type: ignore
    def new_hints(self: HasHints) -> PerObjectHintWithSchemaField:
        hints = original.__get__(self).copy()

        if type(self) not in _schema_added:
            # This is a subclass of the device which was wrapped,
            # but wasn't itself wrapped.
            # To support multiinheritance, look up the schema from
            # the baseclasses.
            new_schema: dict = {}
            _parse_parents_schema(type(self), new_schema)
            _schema_added[type(self)] = new_schema

        schema = _schema_added[type(self)]

        hints = copy.deepcopy(original.__get__(self))
        hints["NX_schema"] = schema
        hints["NX_class"] = schema["nx_class"]

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

        def decorator(device_cls: type[T]) -> type[T]:
            if not isinstance(device_cls, HasHints):
                raise TypeError(
                    f"Cannot apply nexus schema to {device_cls} as it "
                    "is not `HasHints`."
                )
            _inheritance_structure[device_cls] = inherit  # type: ignore
            if inherit:
                _add_inherited_schema(device_cls, nx_schema)  # type: ignore

            # Direct validation with parent classes.
            validated_and_substituted = NxGroup.from_dict(nx_schema).model_dump()
            _schema_added[device_cls] = validated_and_substituted  # type: ignore

            _add_nx_schema_and_device_metadata_to_hints(
                cast(type[HasHints], device_cls), validated_and_substituted
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
