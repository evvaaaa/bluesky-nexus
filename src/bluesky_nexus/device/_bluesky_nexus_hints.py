from bluesky.protocols import Hints


class NxHints(Hints):
    """A hints dictionary but with nexus schema filled in."""

    NX_schema: dict
    NX_class: str
