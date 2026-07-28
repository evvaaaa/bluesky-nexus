"""Pydantic schema for validating the dictionary/yaml."""

from ._base_schema import NxBase, NxField, _nx_instrument_to_pydantic_model
from .nx_object import NxObject

NX_INSTRUMENT_TO_PYDANTIC_MODEL = _nx_instrument_to_pydantic_model.copy()

__all__ = ["NxBase", "NxField", "NxObject", "NX_INSTRUMENT_TO_PYDANTIC_MODEL"]
