[![CI](https://github.com/bluesky/bluesky-nexus/actions/workflows/ci.yml/badge.svg)](https://github.com/bluesky/bluesky-nexus/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/bluesky/bluesky-nexus/branch/main/graph/badge.svg)](https://codecov.io/gh/bluesky/bluesky-nexus)
[![PyPI](https://img.shields.io/pypi/v/bluesky-nexus.svg)](https://pypi.org/project/bluesky-nexus)
![License](https://img.shields.io/badge/License-MIT%202.0-blue.svg)

# bluesky_nexus

A package for generating a standard NeXus structure for bluesky plans.

What            | Where
:---:           | :---:
Source          | <https://github.com/bluesky/bluesky-nexus>
PyPI            | `pip install bluesky-nexus`
Documentation   | <https://bluesky.github.io/bluesky-nexus>
Releases        | <https://github.com/bluesky/bluesky-nexus/releases>

## Design Philosophy

- [`bluesky-nexus`](#bluesky_nexus) provides a standardized nexus structure for any bluesky plan.
- A *take it as it is* approach. [`bluesky-nexus`](#bluesky_nexus) can make a structure for any bluesky run. More structure can be imposed on top of this.
- The nexus structure of a device can be defined on the device class. Device structure is ophyd/ophyd-async agnostic.
- The structure can be used by callbacks by subclassing [`NexusCallback`](#bluesky_nexus.callbacks.BlueskyNexusCallback).

<!-- README only content. Anything below this line won't be included in index.md -->

See https://bluesky.github.io/bluesky-nexus for more detailed documentation.
