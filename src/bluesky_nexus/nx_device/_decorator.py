"""A decorator for applying nexus schema to device."""

import inspect
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import yaml
from bluesky.protocols import HasHints
from event_model import PerObjectHint

from bluesky_nexus.nx_schema import NX_ATTRIBUTE_SERIALIZED_PREFIX, NxBase, NxSubEntry

T = TypeVar("T")


_schema_added: weakref.WeakKeyDictionary[type[HasHints], NxBase] = weakref.WeakKeyDictionary()
_inheritance_structure: weakref.WeakKeyDictionary[type[HasHints], bool] = (
    weakref.WeakKeyDictionary()
)


def _sum_parent_schema[T](cls: type[T], schema: NxBase | None = None) -> NxBase | None:
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


def _add_nx_schema_getter_and_device_metadata_to_hints[T](device_cls: type[T]) -> None:
    original = device_cls.hints  # type: ignore

    @property  # type: ignore
    def new_hints(self: HasHints) -> PerObjectHint:
        hints = original.__get__(self).copy()

        if type(self) not in _schema_added:
            # This is a subclass of the device which was wrapped,
            # but wasn't itself wrapped.
            # To support multinheritance, look up the schema from
            # the baseclasses. This only has to happen the first time
            # hints are called on any of the instances of the class.
            new_schema = _sum_parent_schema(type(self))

            _schema_added[type(self)] = new_schema or NxSubEntry()

        raw_schema = _schema_added[type(self)].model_dump()

        hints["NX_schema"] = raw_schema
        hints["NX_class"] = raw_schema[f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass"]

        return cast(PerObjectHint, hints)

    device_cls.hints = new_hints  # type: ignore


class NexusDevices:
    """
    Static class for adding nexus schema to devices.
    This can be done `from_path` or `from_dictionary` directly.
    """

    @classmethod
    def add_device_from_schema(
        cls, nx_schema: str | Path | dict | NxBase
    ) -> Callable[[type[T]], type[T]]:
        if isinstance(nx_schema, str | Path):
            return cls.add_device_from_path(Path(nx_schema))
        if isinstance(nx_schema, dict):
            return cls.add_device_from_dictionary(nx_schema)
        if isinstance(nx_schema, NxBase):
            return cls.add_device_from_pydantic_schema(nx_schema)

    @classmethod
    def add_device_from_pydantic_schema(
        cls, nx_schema: NxBase, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        def decorator(device_cls: type[T]) -> type[T]:
            if not isinstance(device_cls, HasHints):
                raise TypeError(
                    f"Cannot apply nexus schema to {device_cls} as it is not `HasHints`."
                )

            _inheritance_structure[device_cls] = inherit  # type: ignore
            maybe_with_parents = (
                _sum_parent_schema(cast(type[HasHints], device_cls), nx_schema)
                if inherit
                else nx_schema
            )

            _schema_added[cast(type[HasHints], device_cls)] = maybe_with_parents  # type: ignore

            _add_nx_schema_getter_and_device_metadata_to_hints(cast(type[HasHints], device_cls))

            return device_cls

        return decorator

    @classmethod
    def add_device_from_dictionary(
        cls, nx_schema: dict, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen nx_schema dictionary into the hints of the decorated device.

        If `inherit` then parent device schema will be included.
        """

        deserialized = NxBase.from_dictionary(nx_schema)
        return cls.add_device_from_pydantic_schema(deserialized, inherit=inherit)

    @classmethod
    def add_device_from_path(
        cls, nx_schema: str | Path, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen nx_schema from a given path either absolute across the files system, or
        relative to the device definition/where this wrapper is called from.

        If `inherit` then parent device schema will be included.
        """

        this_file = Path(__file__).resolve()
        frame = inspect.currentframe()
        if not frame:
            raise ValueError(f"Cannot parse {nx_schema} either relative nor absolute.")
        caller_file = None
        # skip current frame and walk back
        frame = frame.f_back
        while frame:
            try:
                fpath = Path(frame.f_code.co_filename).resolve()
            except Exception:
                frame = frame.f_back
                continue
            if fpath != this_file:
                caller_file = fpath
                break
            frame = frame.f_back

        base_dir = caller_file.parent if caller_file is not None else Path.cwd()
        path = (base_dir / Path(nx_schema)).resolve()

        if not path.exists():
            raise ValueError(f"Path `{path.absolute()}` does not exist.")
        with path.open("r") as f:
            loaded_dictionary = yaml.safe_load(f)
        return cls.add_device_from_dictionary(loaded_dictionary, inherit=inherit)
