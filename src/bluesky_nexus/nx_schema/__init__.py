"""Contains the bluesky nexus schema model.

It's assumed any bluesky device corresponds to a subclass of `NxGroup`, containing `NxAttribute`s,
`NxField`s (which in run can contain attributes), and sub `NxGroup`.

For an example implementation of defined schema representing a set of nxdl, see
`bluesky_nexus/nx_nexusformat_schema`, which are schema defined for nexusformat's nxdl:

https://manual.nexusformat.org/classes/base_classes/complete-structure.html

and the default used by this package.
"""

from ._nx_attribute import NX_ATTRIBUTE_SERIALIZED_PREFIX, NxAttribute, NxConstantAttribute
from ._nx_field import NxField
from ._nx_group import NxGroup, add_nx_class_basemodel

__all__ = [
    "NX_ATTRIBUTE_SERIALIZED_PREFIX",
    "NxAttribute",
    "NxConstantAttribute",
    "NxField",
    "NxGroup",
    "add_nx_class_basemodel",
]
