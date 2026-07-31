"""Contains schema for a bluesky nx field."""

from pydantic import BaseModel


class NxField(BaseModel):
    """Represents a datakey which corresponds to a nexus field type."""

    datakey: str
    """The bluesky datakey. The '<name>' in this string will be swapped with the
    object name."""

    nx_alias: str
    """The name which is used as the alias"""

    nx_units: str | None = None
    """An optional units field. By default the units from the bluesky
    document model will be used, but this can be used to override them
    in the event they aren't specified there.
    """
