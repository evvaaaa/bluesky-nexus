from ._base_schema import NxBase, add_as_instrument_class
from pydantic import Field
from typing import Literal


@add_as_instrument_class
class NxObject(NxBase):
    """Represents a NeXus group node."""

    nx_class: Literal["nx_object"] = Field("nx_object")
