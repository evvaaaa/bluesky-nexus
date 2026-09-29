from dataclasses import dataclass
from typing import Any


@dataclass
class NxConstant:
    """For defining a declarative constant in an NxDevice."""

    constant: Any
    """The constant value which will appear in the nexus structure."""


@dataclass
class NxDataKey:
    """For defining a declarative datakey to nexus map in an NxDevice."""

    nx_name: str
    """The name the subdevice should use in NeXus."""


@dataclass
class NxSubDevice:
    """For defining a declarative subdevice in an NxDevice."""

    nx_name: str

    def __init__(self) -> None:
        # TODO: Implemenet
        raise NotImplementedError(
            "This is not yet implemented, it was only just recently added to ophyd-async."
        )
