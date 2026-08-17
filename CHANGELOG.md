# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- Replace this sections with actual changelog entries as the project evolves. -->
## [Unreleased]

## [1.0.0] - 2026-01-20
### Added
- `calculate_stats` function for calculating mean and std dev.
- Unit tests for `calculate_stats` in `tests/test_math_ops.py`.

### Changed
- Refactored project structure to use `src/` layout.
- Updated `pyproject.toml` to include `pytest` and `ruff` as dev dependencies.

### Fixed
- Fixed an issue where `normalize_vector` would crash on zero-length vectors.

## [0.1.0] - 2025-12-15
### Added
- Initial project release.
- Basic `normalize_vector` function.
