"""Module: nx_off_geometry_model.

This module defines the `NXoff_geometryModel`, which represents the geometry
data for 3D objects in the Nexus data format, specifically for storing and
organizing data related to 3D models in the OFF (Object File Format) structure.
The model contains information about the vertices, faces, and other geometric
properties of the 3D object, such as the winding order and detector face
association.

It is used within the Bluesky Nexus framework to store experimental data
related to the geometry of objects used in scientific experiments, such as
detectors, scattering objects, or other relevant components in 3D space.

Classes:
    NXoff_geometryModel (NXgroupModel):
        A class that models the geometry of 3D objects in the OFF format.
"""

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    ConfigDict,
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


# pylint: disable=invalid-name
class NXoff_geometryModel(NXgroupModel):
    """NXoff_geometryModel.

    It represents the geometric data for a 3D object
    in the OFF format, which is used to store information about
    vertices, faces, and their relationships. This class is structured
    to support the storage of detailed geometric properties of the
    object, including the winding order of the faces and detector face
    associations.

    The model includes:
        - Vertices: The 3D coordinates of the vertices that make up the object.
        - Winding Order: The indices of the vertices that define the face in
            the correct order (right-hand rule for normal).
        - Faces: The face indices that define the shape of the object.
        - Detector Faces: Associations between faces and detector IDs.

    Attributes:
        default (NXattrModel): The default attribute for the geometry model,
                                set to "faces".
        vertices (Optional[NXfieldModelWithPrePostRunString]): A list of 3D
                  coordinates (x, y, z) for the vertices of the object.
        winding_order (Optional[NXfieldModelWithPrePostRunString]): A list of
                      vertex indices used to form each face, following the
                      right-hand rule for the face normal.
        faces (Optional[NXfieldModelWithPrePostRunString]): A list that
        indicates the start index in `winding_order` for each face.
        detector_faces (Optional[NXfieldModelWithPrePostRunString]): A list of
                        pairs of indices in the `faces` dataset and the
                        corresponding detector ID.
        model_config (ConfigDict): Configuration for the model, allowing
                                   arbitrary types and forbidding extra fields.
    """

    default: NXattrModel = Field(NXattrModel(value="faces"), description="Default")
    vertices: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="List of x,y,z coordinates for vertices."
    )
    winding_order: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="List of indices of vertices in the vertices dataset to "
        "form each face, right-hand rule for face normal.",
    )
    faces: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="The start index in winding_order for each face."
    )
    detector_faces: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="List of pairs of index in the 'faces' dataset and " "detector id.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
