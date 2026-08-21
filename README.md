# bluesky-nexus

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)<!-- Project badges hosted on codebase.helmholtz.cloud -->
[![Docs](https://img.shields.io/badge/docs-sphinx-blue)](docs/)

<!--- docs index include start -->

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Latest Release](https://codebase.helmholtz.cloud//bluesky_nexus/-/badges/release.svg)](https://codebase.helmholtz.cloud//bluesky_nexus/-/releases)
[![coverage report](https://codebase.helmholtz.cloud//bluesky_nexus/badges/main/coverage.svg)](https://codebase.helmholtz.cloud//bluesky_nexus/-/commits/main)
[![pipeline status](https://codebase.helmholtz.cloud//bluesky_nexus/badges/main/pipeline.svg)](https://codebase.helmholtz.cloud//bluesky_nexus/-/commits/main)

`bluesky_nexus` is a package for generating a standard NeXus structure for bluesky plans.

## Design Philosophy

- [`bluesky-nexus`](#bluesky_nexus) provides a standardized nexus structure for any bluesky plan.
- A *take it as it is* approach. [`bluesky-nexus`](#bluesky_nexus) can make a structure for any bluesky run. More structure can be imposed on top of this.
- The nexus structure of a device can be defined on the device class. Device structure is ophyd/ophyd-async agnostic.
- The structure can be used by callbacks by subclassing [`NexusCallback`](#bluesky_nexus.BlueskyNexusCallback).

<!--- docs index include end -->

## Contributing

Please see the [CONTRIBUTING.md](docs/CONTRIBUTING.md) file for contribution guidelines.
