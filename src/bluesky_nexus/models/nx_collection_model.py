"""
Module: nx_collection_model.py.

This module defines the `NXcollectionModel`, a specialized extension of
`NXgroupModel` for representing collections of NeXus groups within a
scientific dataset. It provides flexibility for handling arbitrary types
while ensuring compatibility with NeXus standards.

### Features:
- **Extends NXgroupModel**: Inherits all properties and validation rules
  of `NXgroupModel`.
- **Arbitrary Type Support**: Uses `ConfigDict` to allow additional types
  and properties.
- **Flexible Structure**: Designed to accommodate complex NeXus collections.

### Main Model:
- `NXcollectionModel`: A subclass of `NXgroupModel` with extended
  configurability.

This module is intended to provide a structured approach to handling NeXus
collections within data processing workflows.
"""

from bluesky_nexus.models.nx_core_models import (
    ConfigDict,
    NXgroupModel,
)


class NXcollectionModel(NXgroupModel):
    """NXcollectionModel.

    A specialized NeXus group model representing a collection of NeXus groups.

    This model extends `NXgroupModel` to allow more flexible configurations
    and arbitrary types while maintaining NeXus compatibility.

    Attributes:
    - Inherits all attributes from `NXgroupModel`.
    - `model_config`: Configures the model to allow additional types and
      properties.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
