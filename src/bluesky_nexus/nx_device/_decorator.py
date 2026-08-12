"""A decorator for applying nexus schema to device."""

import weakref
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import yaml
from bluesky.protocols import HasHints
from event_model import PerObjectHint

from bluesky_nexus.nx_schema._nx_classes.nx_object import NxObject
from bluesky_nexus.nx_schema.nx_base import NxBase

T = TypeVar("T")


_schema_added: weakref.WeakKeyDictionary[type[HasHints], NxBase] = weakref.WeakKeyDictionary()
_inheritance_structure: weakref.WeakKeyDictionary[type[HasHints], bool] = (
    weakref.WeakKeyDictionary()
)


def _sum_parent_schema(cls: type[T], schema: NxBase | None = None) -> NxBase | None:
    for direct_parent in cls.__bases__:
        if _inheritance_structure.get(direct_parent) is not False:
            maybe_parent_schema = _sum_parent_schema(direct_parent, schema=schema)
            if maybe_parent_schema and schema:
                schema += maybe_parent_schema
            elif not schema and maybe_parent_schema:
                schema = maybe_parent_schema

        if schema_added := _schema_added.get(direct_parent):
            if schema:
                schema += schema_added
            else:
                schema = schema_added

    return schema


def _add_nx_schema_getter_and_device_metadata_to_hints(device_cls: type[T]) -> None:
    original = device_cls.hints  # type: ignore

    @property  # type: ignore
    def new_hints(self: HasHints) -> PerObjectHint:
        hints = original.__get__(self).copy()
        if hasattr(self, "md"):
            hints["md"] = self.md  # type: ignore

        if type(self) not in _schema_added:
            # This is a subclass of the device which was wrapped,
            # but wasn't itself wrapped.
            # To support multinheritance, look up the schema from
            # the baseclasses.
            new_schema = _sum_parent_schema(type(self))

            _schema_added[type(self)] = new_schema or NxObject()

        raw_schema = _schema_added[type(self)].model_dump()

        hints["NX_schema"] = raw_schema
        hints["NX_class"] = raw_schema["@nxclass"]

        return cast(PerObjectHint, hints)

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
                    f"Cannot apply nexus schema to {device_cls} as it is not `HasHints`."
                )

            # Validation without parent classes.
            validated_and_substituted = NxBase.from_dict(nx_schema)

            _inheritance_structure[device_cls] = inherit  # type: ignore
            if inherit:
                validated_and_substituted = _sum_parent_schema(
                    cast(type[HasHints], device_cls), validated_and_substituted
                )
                assert validated_and_substituted is not None

            _schema_added[cast(type[HasHints], device_cls)] = validated_and_substituted

            _add_nx_schema_getter_and_device_metadata_to_hints(cast(type[HasHints], device_cls))
            return device_cls

        return decorator

    @classmethod
    def from_path(cls, path: str | Path, inherit: bool = True) -> Callable[[type[T]], type[T]]:
        """Load the chosen nx_schema path into the hints of the decorated device.

        If `inherit` then parent device schema will be included.
        """
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Path `{path}` does not exist.")
        with path.open("r") as f:
            nx_schema = yaml.safe_load(f)
        return cls.from_dictionary(nx_schema, inherit=inherit)
