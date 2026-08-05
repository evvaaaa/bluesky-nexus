"""Tests with different kinds of plan.

"simple" reads/one shots on standard readables are well enough tested in other files.

This tests for e.g, flyers where events are collected, flyers where external asset
documents are generated, event_pages are made, a devices configuration is provided
twice etc.
"""

from bluesky import RunEngine


def test_descriptor_reconfiguration(RE_directly_subscribed: RunEngine): ...
