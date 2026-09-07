"""Contains the basemodel for ``NxInternalLink``.

An ``NxInternalLink`` allows for the creation of internal links inside a device.

The link is relative to the root of the device. Devices referencing fields in other
devices this way is not supported.
"""

from typing import Any

from pydantic import model_serializer

from ._nx_attribute import (
    prepend_serialized_prefix_to_nx_attributes,
)
from ._nx_base import NxBase

NX_LINK_SERIALIZED_PREFIX = "&"


def prepend_serialized_prefix_to_nx_internal_links(name: str, value: Any) -> str:
    """Adds the serialized prefix to a given name if the value is an `NxInternalLink`."""
    return f"{NX_LINK_SERIALIZED_PREFIX}{name}" if isinstance(value, NxInternalLink) else name


class NxInternalLink(NxBase):
    """A hard link to some other nexus object in the schema.

    https://manual.nexusformat.org/design.html#links

    The reference is absolute from the root of the device.
    """

    link: list[str]

    @model_serializer
    def _use_link_shorthand(self) -> dict[str, Any]:
        """Dump the schema with short-hand.

        * `foo: NxInternalLink(link="bar")` -> `&foo: "bar"`
        """
        shortened = {}
        for key, value in self:
            key = prepend_serialized_prefix_to_nx_attributes(key, value)
            match value:
                case NxInternalLink(link=link):
                    shortened[key] = link
                case None if key in NxInternalLink.model_fields:
                    continue  # Value is `None` for unused field.
                case _:
                    shortened[key] = value

        return shortened
