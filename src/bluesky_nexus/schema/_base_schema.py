"""
This module contains the NxBase class, which has the most basic validation on the
structure all device schema must correspond to of the schema.


When nx_instrument is specified in the schema, the correct nexus class is automatically
selected and initialized by `NxBase.from_dictionary`.
This module contains a decorator for appending different instrument schema basemodels to
a global dictionary.
"""

from __future__ import annotations
from functools import cached_property
from typing import Any, Callable, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class NxField(BaseModel):
    """Represents a datakey which corresponds to a nexus field type."""

    datakey: str
    """The bluesky datakey the name of the device should be swapped with <obj>."""

    nx_alias: str | None = None
    """An optional alias."""

    nx_units: str | None = None
    """An optional units field. By default the units from the bluesky
    document model will be used, but this can be used to override them
    in the event they aren't specified there.
    """


T = TypeVar("T", bound="NxBase")

_DIRECT_ADDITION_FIELDS = frozenset(["nx_class"])
"""Fields which should be directly added as key value."""


class NxBase(BaseModel):
    """Validates the nexus schema of a device.

    If `nx_instrument` is specified it will use the instrument of the same
    name in this class. Otherwise it will not do any validation other than
    check that the dictionary will be parsable by the callback.
    """

    nx_class: str = Field("NxObject")
    """The nexus baseclass of this group."""

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls: type[T], dictionary: dict[str, Any]) -> T:
        """Load a dictionary into a basemodel."""
        kwargs = {}
        document_cls: type[NxBase] = cls

        for key, value in dictionary.items():
            if key == "nx_instrument":
                nx_instrument = value
                maybe_document_cls = _nx_instrument_to_pydantic_model.get(nx_instrument)
                if maybe_document_cls is None:
                    raise TypeError(
                        f"Requested `nx_instrument: {nx_instrument}` but this isn't "
                        "defined to have a pydantic schema. Remove this key to only "
                        "use primative validation."
                    )
                document_cls = maybe_document_cls
            elif value is None:
                kwargs[key] = NxField(datakey=key)
            elif isinstance(value, dict) and (nx_alias := value.get("nx_alias")):
                kwargs[key] = NxField(datakey=key, nx_alias=nx_alias)
            elif isinstance(value, dict):
                kwargs[key] = NxBase.from_dict(value)
            elif key in _DIRECT_ADDITION_FIELDS:
                kwargs[key] = value

        return document_cls(**kwargs)  # type: ignore


_nx_instrument_to_pydantic_model: dict[str, type[NxBase]] = {}


def add_as_instrument_class(cls: type[NxBase]) -> Callable[[], None]:
    def decorator() -> None:
        instrument_name = cls.__qualname__
        if already_present := _nx_instrument_to_pydantic_model.get(instrument_name):
            raise TypeError(
                f"{cls.__module__}.{cls.__qualname__} cannot be added as an instrument "
                "as it's already present as "
                f"{already_present.__module__}.{already_present.__qualname__}"
            )
        _nx_instrument_to_pydantic_model[instrument_name] = cls

    return decorator
