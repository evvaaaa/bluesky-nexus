from typing import Literal

from pydantic import Field

from ._base_schema import NxBase, add_as_instrument_class


@add_as_instrument_class
class NxObject(NxBase):
    """Represents a NeXus group node."""

    nx_class: Literal["nx_object"] = Field("nx_object")
