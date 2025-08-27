"""
Module: nx_transformations_model.

This module defines the `NXtransformationsModel`, which is used to describe
the transformations applied to a set of data in the Nexus format. Specifically,
the model captures information about geometric transformations, such as
translations and rotations, that are applied to an axis or a set of axes.

The model allows for the specification of the type of transformation, the
axis of transformation, the vector defining the axis, and other relevant
parameters such as offsets, units, and dependencies. It is structured to
represent transformations in the context of experimental setups, such as
detectors, equipment components, or other related transformations in scientific
experiments.

Classes:
    NXtransformationsModel (NXgroupModel):
        A class representing transformations, such as translation and rotation,
        in an experimental setup. The transformation is defined by attributes
        like the transformation type, vector, offset, and associated equipment.

    AXISNAMEModel (NXfieldModelWithPrePostRunString):
        A model that represents the specifics of the axis on which the
        transformation is applied. Includes attributes like transformation
        type, vector, offset, and equipment component.
"""

# pylint: disable=duplicate-code

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    BaseModel,
    ConfigDict,
    Field,
    NXattrModel,
    NXfieldModelForAttribute,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


class NXtransformationsModel(NXgroupModel):
    """NXtransformationsModel.

    It represents geometric transformations
    applied to data in an experimental context. This includes
    transformations like translation (linear displacements) and rotation
    (angular rotations) along specific axes. The transformations are
    parameterized by axis definitions, vectors, offsets, and additional
    configuration details, such as dependencies on other fields or
    components of the equipment.

    Attributes:
        default (NXattrModel): The default attribute for the transformation
            model, set to "vector".
        AXISNAME (Optional[AXISNAMEModel]): A model that describes a specific
            axis and the transformation applied to it, including the type of
            transformation, vector, and optional offset.
        AXISNAME_end (Optional[NXfieldModelWithPrePostRunString]):
        A placeholder for a name constructed by appending '_end' to the axis
        name.
        AXISNAME_increment_set (Optional[NXfieldModelWithPrePostRunString]): A
            placeholder for a name constructed by appending '_increment_set' to
            the axis name.
        model_config (ConfigDict): Configuration for the model, allowing
            arbitrary types and forbidding extra fields.
    """

    default: NXattrModel = Field(NXattrModel(value="alpha"), description="Default")

    # ----- AXISNAME -----
    class AXISNAMEModel(NXfieldModelWithPrePostRunString):
        """AXISNAMEModel.

        It represents the details of a specific axis in a
        transformation.

        This includes the overall structure of the axis name and the
        transformation applied to it.
        """

        class AttributesModel(BaseModel):
            """AttributesModel.

            It defines the transformation-specific
            details for the axis in the transformation. These include
            the type of transformation (translation or rotation), the
            axis vector, optional offsets, and additional configuration
            parameters.

            Attributes:
                transformation_type (Optional[NXfieldModelForAttribute]): The
                type of transformation, either 'translation' or 'rotation'.
                vector (NXfieldModelForAttribute): The three values that define
                the axis for the transformation.
                offset (Optional[NXfieldModelForAttribute]): A fixed offset
                applied before the transformation.
                offset_units (Optional[NXfieldModelForAttribute]): Units for
                the offset.
                depends_on (Optional[NXfieldModelForAttribute]): Path to a
                field that defines the axis of dependence.
                equipment_component (Optional[NXfieldModelForAttribute]):
                Identifier for the component of equipment.
                description (Optional[NXfieldModelForAttribute]):
                    A textual description of the axis and its purpose.
                units (Optional[NXfieldModelForAttribute]):
                    The measurement units used for the axis values.
                model_config (ConfigDict): Configuration for the axis model,
                allowing arbitrary types and forbidding/permitting extra
                fields.
            """

            transformation_type: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="The transformation_type may be translation, in "
                "which case the values are linear displacements along the "
                "axis, rotation, in which case the values are angular "
                "rotations around the axis.",
            )
            vector: NXfieldModelForAttribute = Field(
                ...,
                description="Three values that define the axis for this "
                "transformation.",
            )
            offset: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="A fixed offset applied before the transformation "
                "(three vector components).",
            )
            offset_units: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="Units of the offset. Values should be consistent "
                "with NX_LENGTH.",
            )
            depends_on: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="Points to the path to a field defining the axis "
                "on which this depends or the string “.”.",
            )
            equipment_component: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="An arbitrary identifier of a component of the "
                "equipment to which the transformation belongs, such as "
                "‘detector_arm’ or ‘detector_module’.",
            )

            # Custom additions
            description: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="A textual description of the axis and its " "purpose.",
            )
            units: Optional[NXfieldModelForAttribute] = Field(
                None,
                description="The measurement units used for the axis values.",
            )
            model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

        attributes: Optional[AttributesModel] = Field(
            None, description="Attributes specific to the 'AXISNAME' field."
        )

    alpha: Optional[AXISNAMEModel] = Field(
        None,
        description="Units need to be appropriate for translation or " "rotation.",
    )
    alpha_end: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_end is a placeholder for a name constructed "
        "from the actual name of an axis to which _end has been appended.",
    )
    alpha_increment_set: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_increment_set is a placeholder for a name "
        "constructed from the actual name of an axis to which _increment_set "
        "has been appended.",
    )

    beta: Optional[AXISNAMEModel] = Field(
        None,
        description="Units need to be appropriate for translation or " "rotation.",
    )
    beta_end: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_end is a placeholder for a name constructed "
        "from the actual name of an axis to which _end has been appended.",
    )
    beta_increment_set: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_increment_set is a placeholder for a name "
        "constructed from the actual name of an axis to which _increment_set "
        "has been appended.",
    )

    theta: Optional[AXISNAMEModel] = Field(
        None,
        description="Units need to be appropriate for translation or " "rotation.",
    )
    theta_end: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_end is a placeholder for a name constructed "
        "from the actual name of an axis to which _end has been appended.",
    )
    theta_increment_set: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="AXISNAME_increment_set is a placeholder for a name "
        "constructed from the actual name of an axis to which _increment_set "
        "has been appended.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
