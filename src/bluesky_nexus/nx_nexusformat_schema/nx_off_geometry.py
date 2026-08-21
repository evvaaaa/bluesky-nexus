"""Contains the definition for NXoff_geometry."""

from bluesky_nexus.nx_schema import (
    NxField,
    add_nx_class_basemodel,
)

from .nx_object import NxObject


@add_nx_class_basemodel
class NxOff_Geometry(NxObject):
    """Represents a NeXus NXoff_geometry."""

    vertices: NxField | None = None
    """List of x,y,z coordinates for vertices. The origin of the coordinates is the
    position of the parent component, for example the NXdetector which the geometry describes."""

    winding_order: NxField | None = None
    """List of indices of vertices in the vertices dataset to
    form each face, right-hand rule for face normal."""

    faces: NxField | None = None
    """The start index in `winding_order` for each face."""

    detector_faces: NxField | None = None
    """List of pairs of index in the “faces” dataset and detector id.
    This dataset should only be used only if the NXoff_geometry group is describing a detector.
    """
