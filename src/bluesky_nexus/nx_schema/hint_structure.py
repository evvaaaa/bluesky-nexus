"""The typed dict for the per object hint we expect."""

from typing import Literal, NotRequired, TypedDict

from event_model import PerObjectHint


class NxFieldInHints(TypedDict, total=True):
    """Typeddict for an NxField.

    Stored in an `NxGroup` (below) with the datakey name as
    the key.
    """

    datakey: str
    nx_alias: str
    nx_units: str | None
    nx_class: Literal["NXfield"]


class NxGroupInHints(TypedDict, total=False):
    """TypedDict for a nexus group. Other fields are either
    specifying `NXfield` or sub `NxGroup`.
    """

    nx_class: str


class PerObjectHintWithSchemaField(PerObjectHint):
    """Hints with a nexus group."""

    NX_schema: NotRequired[NxGroupInHints]
