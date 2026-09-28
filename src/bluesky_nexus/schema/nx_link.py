"""Contains the basemodel for ``NxInternalLink``.

An ``NxInternalLink`` allows for the creation of internal links inside a device.

The link is relative to the root of the device. Devices referencing fields in other
devices this way is not supported.
"""

from pprint import pformat
from typing import Any, Self

from pydantic import model_validator

from ._nx_base import ALPHA_NUMERIC_WITH_UNDERSCORES, NxBase

NX_LINK_SERIALIZED_PREFIX = "&"


def prepend_serialized_prefix_to_nx_links(name: str, value: Any) -> str:
    """Adds the serialized prefix to a given name if the value is an `NxInternalLink`."""
    return (
        f"{NX_LINK_SERIALIZED_PREFIX}{name}"
        if isinstance(value, NxInternalLink | NxDeviceLink)
        else name
    )


class _NxLinkBase(NxBase):
    @classmethod
    def _allowed_value_types(cls) -> tuple[type | None, ...]:
        """NxLink cannot contain any additional field types, even NxAttribute."""
        return ()


class NxInternalLink(_NxLinkBase):
    """A hard link to some other nexus object internal to the device schema
    schema.

    https://manual.nexusformat.org/design.html#links

    The reference is absolute from the root of the device which
    the structure is generating.

    In the group schema, the following shorthand is applied:

    * `foo: NxInternalLink(link=["bar"])` -> `&foo: ["bar"]`
    """

    link: list[str]


class NxDeviceLink(_NxLinkBase):
    """A hard link to a nexus device object which will be
    generated in the schema.

    https://manual.nexusformat.org/design.html#links

    The reference is absolute from devices/ in the NeXus structure,
    e.g foo=NxDeviceLink("some_device", stream="baseline") creates a link
    into "devices/baseline/some_device" in the final NeXus structure.

    In the application schema, the following shorthand is applied:

    * `foo: NxDeviceLink(link=["bar"], stream="primary")` -> `&foo: ["bar"]`
    * `foo: NxDeviceLink(link=["bar"], stream="baseline")`
            -> `&foo: {link: ["bar"], stream: "primary"}`
    """

    device: str
    stream: str = "primary"

    @model_validator(mode="after")
    def _ensure_device_and_stream_are_alpha_numeric(self) -> Self:
        for attribute_name in ("device", "stream"):
            attribute = getattr(self, attribute_name)
            if not ALPHA_NUMERIC_WITH_UNDERSCORES.match(attribute):
                pretty_key = pformat({"device": self.device, "stream": self.stream})
                raise TypeError(
                    f"Error in given NxLink: {pretty_key} has a {attribute_name} which isn't a "
                    "valid NeXus name."
                )
        return self
