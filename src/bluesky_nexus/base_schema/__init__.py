"""Contains the bluesky nexus schema model.

There are two subpackages:

1. `building_blocks` which contains schema definitions for building the pydantic schema,
2. `fundamental` which contains implementations which should never be possible to be overwritten
    by an institutions own NXDL implementation.

"""

# Building blocks, abstract classes for defining schema,
# or implementations of what is allowed in schema attributes.

from ._building_blocks.nx_attribute import (
    NX_ATTRIBUTE_SERIALIZED_PREFIX,
    NxAttribute,
    NxConstantAttribute,
)
from ._building_blocks.nx_field import NxField
from ._building_blocks.nx_group import NX_CLASS_TO_BASEMODEL, NxGroup, add_nx_class_basemodel
from ._building_blocks.nx_link import NxInternalLink
from ._fundamental.nx_component import NxComponent

# Fundamental definitions, schema which should never be overwritten
# in other NXDL.
from ._fundamental.nx_data import NxData
from ._fundamental.nx_log import NxLog, NxTimeField
from ._fundamental.nx_object import NxObject

__all__ = [
    "NX_ATTRIBUTE_SERIALIZED_PREFIX",
    "NxAttribute",
    "NxConstantAttribute",
    "NxField",
    "NxGroup",
    "add_nx_class_basemodel",
    "NX_CLASS_TO_BASEMODEL",
    "NxInternalLink",
    "NxData",
    "NxLog",
    "NxTimeField",
    "NxObject",
    "NxComponent",
]
