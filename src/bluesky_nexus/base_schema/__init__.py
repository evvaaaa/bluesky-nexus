"""Contains the bluesky nexus schema model.

It's assumed any bluesky device corresponds to a subclass of `NxGroup`, containing `NxAttribute`s,
`NxField`s (which in turn can contain attributes), and subgroups of `NxGroup`.

Implementations of specific NXDL schema then use these base classes to define their schema
model.

For an example implementation of defined schema representing a set of nxdl, see
``bluesky_nexus/nexusformat_schema``, which are schema defined for nexusformat's nxdl:

https://manual.nexusformat.org/classes/base_classes/complete-structure.html

nexusformat NXDL is given in with this package through ``bluesky_nexus.nexusformat_schema``.
It is a design goal for `bluesky_nexus` to be able to load other sets of schema definitions
in future.
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
