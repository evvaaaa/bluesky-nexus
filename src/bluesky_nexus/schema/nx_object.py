"""Contains the definition for `NXObject`."""

from typing import Literal

from pydantic import Field

from .nx_group import NxGroup, add_nx_class_basemodel


@add_nx_class_basemodel
class NxObject(NxGroup):
    """Represents a NeXus group node."""

    nx_class: Literal["NXobject"] = Field("NXobject")
