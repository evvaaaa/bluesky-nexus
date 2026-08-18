"""Contains the basemodel for `NxAttribute`.

An NxAttribute is a leaf in the bluesky nexus schema which acts as a piece of
metadata in the NxBase it's contained in.
"""

from typing import Any, TypeVar

from ._nx_base_leaf import NxBaseLeaf

T = TypeVar("T", bound=Any)


def prepend_serialized_prefix_to_nx_attributes(name: str, value: Any) -> str:
    """Adds the serialized prefix to a given name if the value is an `NxAttribute`."""
    return f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}{name}" if isinstance(value, NxAttribute) else name


NX_ATTRIBUTE_SERIALIZED_PREFIX = "$"
"""If a key in the serialized schema contains this prefix then it's a
NeXus attribute."""


class NxAttribute(NxBaseLeaf):
    """An attribute which can be defined on any `NxField` or `NxGroup`

    When an `NxBase` is serialized it's `NxAttribute` keys are prepended with "$".
    """


class NxConstantAttribute[T: Any](NxAttribute):
    """An NxAttribute which has to be constant valued."""

    constant: T
    hints_key: None = None
    data_key: None = None
