from dataclasses import dataclass
from typing import Any


@dataclass
class _NxAnnotation:
    nx_name: Any
    """The name in the final nexus structure that this annotation should map
    the python attribute to."""

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """An unused call method to match the DeviceAnnotation protocol."""


@dataclass
class NxConstant(_NxAnnotation):
    """For defining a declarative constant in an NxDevice."""

    is_nx_attribute: bool = False
    """Whether this should become an attribute in the group instead of a field."""


@dataclass
class NxDataKey(_NxAnnotation):
    """For defining a declarative datakey to nexus map in an NxDevice."""

    is_nx_attribute: bool = False
    """Whether this should become an attribute in the group instead of a field."""


@dataclass
class NxSubGroup(_NxAnnotation):
    """For defining a declarative subdevice/subgroup in an NxDevice."""
