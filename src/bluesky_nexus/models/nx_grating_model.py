"""nx_grating_model.

nx_grating_model: Model for organizing grating-related metadata and
configuration.

This module defines a model for organizing and managing metadata and
configuration specifically related to optical gratings. It provides a flexible
structure for handling various attributes of gratings used in optical systems,
such as grating parameters, material properties, diffraction characteristics,
and dependencies. This model also allows integration with other related models
such as transformations and off-geometry definitions.

Class:
    - NXgratingModel: A model for managing metadata and configuration related
      to optical gratings, including material properties, grating geometry,
      and transformations.
"""

# pylint: disable=duplicate-code

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    ConfigDict,
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)
from bluesky_nexus.models.nx_data_model import NXdataModel
from bluesky_nexus.models.nx_off_geometry_model import NXoff_geometryModel
from bluesky_nexus.models.nx_transformations_model import (
    NXtransformationsModel,
)


class NXgratingModel(NXgroupModel):
    """NXgratingModel.

    Model for managing grating-related metadata and configuration.

    This class provides a flexible structure for managing metadata and
    configuration for optical gratings in a system. It supports various
    attributes, including material properties, diffraction
    characteristics, and transformation settings. The model allows
    customization through a configuration that accepts arbitrary types
    and extra fields for a wide range of grating parameters and
    dependencies.
    """

    default: NXattrModel = Field(
        NXattrModel(value="diffraction_order"), description="Default."
    )
    angles: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Blaze or trapezoidal angles, with the angle of the "
        "upstream facing edge listed first. Blazed gratings can be identified "
        "by the low value of the first-listed angle.",
    )
    period: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="List of polynomial coefficients describing the spatial "
        "separation of lines/grooves as a function of position along the "
        "grating, in increasing powers of position. Gratings which do not "
        "have variable line spacing will only have a single coefficient "
        "(constant).",
    )
    duty_cycle: Optional[NXfieldModelWithPrePostRunString] = Field(None)
    depth: Optional[NXfieldModelWithPrePostRunString] = Field(None)
    diffraction_order: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Diffraction order."
    )
    deflection_angle: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Angle between the incident beam and the utilised "
        "outgoing beam.",
    )
    interior_atmoshpere: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Any of these values: vacuum | helium | argon."
    )
    substrate_material: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Substrate material type."
    )
    substrate_density: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="substrate_density."
    )
    substrate_thickness: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="substrate_thickness."
    )
    coating_material: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="coating_material."
    )
    substrate_roughness: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="substrate_roughness."
    )
    coating_roughness: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="coating_roughness."
    )
    layer_thickness: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="An array describing the thickness of each layer."
    )
    depends_on: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="NeXus positions components by applying a set of "
        "translations and rotations to apply to the component starting "
        "from 0, 0, 0.",
    )
    figure_data: Optional[NXdataModel] = Field(
        None,
        description="Numerical description of the surface figure " "of the mirror.",
    )
    OFF_GEOMETRY: Optional[NXoff_geometryModel] = Field(
        None,
        description="This group describes the shape of the beam line " "component.",
    )
    TRANSFORMATIONS: Optional[NXtransformationsModel] = Field(
        None,
        description="“Engineering” position of the grating Transformations"
        "used by this component to define its position and orientation.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
