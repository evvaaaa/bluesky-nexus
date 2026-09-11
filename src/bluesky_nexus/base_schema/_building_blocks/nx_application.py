"""
Contains the base class for NeXus application groups.

This can be subclassed to define bluesky nexus application schema corresponding to nxdl schema.

"""

from abc import ABC
from typing import ClassVar, Final

from .nx_group import NxGroup
from .nx_link import NxDeviceLink


class NxApplication(NxGroup, ABC):
    """Base class for NeXus applications."""

    _ALLOWED_LINK_TYPE: Final[ClassVar[type[NxDeviceLink]]] = NxDeviceLink  # type: ignore
    """Specifies the link type which serialized "&" links should go to
    on deserialization. Marked as final so no subclasses will override it further."""
