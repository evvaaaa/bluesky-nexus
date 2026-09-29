"""Contains a decorator for loading bluesky-nexus schema into a device's hints."""

import inspect
import weakref
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar, cast

import yaml
from bluesky.protocols import HasHints
from event_model import PerObjectHint

from bluesky_nexus.logger import LOGGER
from bluesky_nexus.schema import NX_ATTRIBUTE_SERIALIZED_PREFIX, NxGroup

T = TypeVar("T")


_schema_added: weakref.WeakKeyDictionary[type[HasHints], NxGroup | None] = (
    weakref.WeakKeyDictionary()
)
_inheritance_structure: weakref.WeakKeyDictionary[type[HasHints], bool] = (
    weakref.WeakKeyDictionary()
)


def _sum_parent_schema[T](cls: type[T], schema: NxGroup | None = None) -> NxGroup | None:
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


def _add_nx_schema_getter_to_hints[T](device_cls: type[T]) -> None:
    """Patches a ``HasHints`` device class' .hints property with a new one
    which calls the old one, and then appends `NX_class` and `NX_schema`
    fields to the return."""
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

            # TODO: We probably don't have to do this if we start storing the
            # hints as an attribute (in the python sense) on the class itself.
            # This would also be nice because it'd allow other device packages,
            # e.g ophyd-async to come up with their own ways of adding schema,
            # for example declarative definitions on an `ophyd_async.core.StandardReadable`.
            new_schema = _sum_parent_schema(type(self))

            if new_schema is None:
                LOGGER.warning(
                    "Failed to retrieve the parent schema of a device which "
                    "wasn't directly decorated, but has a parent which was decorated."
                    "This should be impossible. Continuing on without schema."
                )
            _schema_added[type(self)] = new_schema
        if (schema := _schema_added[type(self)]) is not None:
            raw_schema = schema.model_dump(exclude_unset=True, exclude_none=True)

            hints["NX_schema"] = raw_schema
            hints["NX_class"] = raw_schema[f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}nxclass"]

        return cast(PerObjectHint, hints)

    device_cls.hints = new_hints  # type: ignore


class NxDevice:
    """Static class for adding nexus schema to devices."""

    @classmethod
    def add_device_from_schema(
        cls, nexus_schema: str | Path | dict | NxGroup, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Adds device schema to the wrapped `HasHints` class.

        Schema can be in any of the accepted formats - a path to yaml, a dict,
        or a basemodel directly.

        If ``inherit`` is ``False`` then don't attempt to add schema from parent classes
        of the ``cls`` class.
        """
        if isinstance(nexus_schema, str | Path):
            return cls.add_device_from_path(Path(nexus_schema), inherit=inherit)
        if isinstance(nexus_schema, dict):
            return cls.add_device_from_dictionary(nexus_schema, inherit=inherit)
        if isinstance(nexus_schema, NxGroup):
            return cls.add_device_from_pydantic_schema(nexus_schema, inherit=inherit)

    @classmethod
    def add_device_from_pydantic_schema(
        cls, nexus_schema: NxGroup, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Adds the `NxGroup` schema, or a subclass of it, to the wrapped `HasHints` class.

        If ``inherit`` is ``False`` then don't attempt to add schema from parent classes
        of the ``cls`` class.
        """

        def decorator(device_cls: type[T]) -> type[T]:
            if not isinstance(device_cls, HasHints):
                raise TypeError(
                    f"Cannot apply nexus schema to {device_cls} as it is not `HasHints`."
                )

            _inheritance_structure[device_cls] = inherit  # type: ignore
            maybe_with_parents = (
                _sum_parent_schema(cast(type[HasHints], device_cls), nexus_schema)
                if inherit
                else nexus_schema
            )

            _schema_added[cast(type[HasHints], device_cls)] = maybe_with_parents  # type: ignore

            _add_nx_schema_getter_to_hints(cast(type[HasHints], device_cls))

            return device_cls

        return decorator

    @classmethod
    def add_device_from_dictionary(
        cls, nexus_schema: dict, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen ``nexus_schema`` dictionary into the hints of the decorated device.

        Schema is validated against the pydantic basemodel.

        If ``inherit`` is ``False`` then don't attempt to add schema from parent classes
        of the ``cls`` class.
        """

        deserialized = NxGroup.from_dictionary(nexus_schema)
        return cls.add_device_from_pydantic_schema(deserialized, inherit=inherit)

    @classmethod
    def add_device_from_path(
        cls, nexus_schema: str | Path, inherit: bool = True
    ) -> Callable[[type[T]], type[T]]:
        """Load the chosen ``nexus_schema`` from a given path either absolute across the files
         system, or relative to the device definition/where this wrapper is called from.

        Schema is validated against the pydantic basemodel.

        If ``inherit`` is ``False`` then don't attempt to add schema from parent classes
        of the ``cls`` class.
        """

        this_file = Path(__file__).resolve()
        frame = inspect.currentframe()
        if not frame:
            raise ValueError(f"Cannot parse {nexus_schema} either relative nor absolute.")
        caller_file = None
        # Skip current frame and walk back to find the path where the decorator
        # is called from.
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

        base_directory = caller_file.parent if caller_file is not None else Path.cwd()
        path = (base_directory / Path(nexus_schema)).resolve()

        if not path.exists():
            raise ValueError(f"Path `{path.absolute()}` does not exist.")
        with path.open("r") as f:
            loaded_dictionary = yaml.safe_load(f)
        return cls.add_device_from_dictionary(loaded_dictionary, inherit=inherit)
