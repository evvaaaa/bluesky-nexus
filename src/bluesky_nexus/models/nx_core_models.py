"""
Module: nx_core_models.py.

This module defines Pydantic models for representing NeXus data structures,
which are commonly used in scientific data formats to organize hierarchical
datasets. These models provide structure, validation, and utilities for
handling NeXus objects, fields, groups, links, and attributes.

### Features:
- **Structured Data Representation**: Provides a consistent model for NeXus
  components.
- **Validation**: Ensures data integrity using Pydantic's validation
  mechanisms.
- **Flexibility**: Supports scalar values, arrays, and hierarchical
  relationships.
- **Integration with HDF5**: Can be used to interact with NeXus files based on
  HDF5.

### Main Models:
- `NXattrModel`: Represents NeXus attributes.
- `NXFileModel`: Represents a NeXus file.
- `NXobjectModel`: Base model for NeXus objects.
- `NXgroupModel`: Represents a NeXus group.
- `NXfieldModel`: Represents a NeXus field.
- `NXfieldModelForAttribute`: A specialized field model for attributes.
- `PrePostRunString`: Custom string type for handling pre- and post-run
  metadata.

This module is designed to facilitate working with NeXus data structures in
Python applications, ensuring consistency and correctness when handling
scientific datasets.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from numpy.typing import ArrayLike
from pydantic import BaseModel, ConfigDict, Field

# from pydantic.core import PydanticSchema  # To be activated for pydantic V3

__all__ = [
    "BaseModel",
    "Scalar",
    "Number",
    "Field",
    "NXattrModel",
    "NXfieldModel",
    "NXfieldModelWithPrePostRunString",
    "NXgroupModel",
    "NXobjectModel",
]

# scalar type
Scalar = Union[str, float, int]

# number type
Number = Union[float, int]


class PrePostRunString(str):
    """PrePostRunString.

    Custom string type representing pre- and post-run strings in
    NeXus metadata.

    This ensures that values must start with one of the following prefixes:
    - "$pre-run-cpt"
    - "$pre-run-md"
    - "$post-run"
    """

    # To be removed in pydantic V3
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    # To be activated for pydantic V3
    # @classmethod
    # def __get_pydantic_core_schema__(cls, schema: PydanticSchema):
    #     # Modify schema to include custom validation logic
    #     schema = schema.clone()
    #     schema.validate = cls.validate
    #     return schema

    @classmethod
    def validate(cls, value: Any, *args, **kwargs) -> "PrePostRunString":
        """Validate the value.

        Ensure it starts with allowed prefixes.
        """
        _ = args
        _ = kwargs

        if not isinstance(value, str):
            raise ValueError("string required")
        if not (
            value.startswith("$pre-run-cpt")
            or value.startswith("$pre-run-md")
            or value.startswith("$post-run")
        ):
            raise ValueError(
                'string must start with "$pre-run-cpt" or $pre-run-md or "$post-run"'
            )
        return cls(value)


class NXattrModel(BaseModel):
    """NXattrModel.

    Pydantic model representing an NXattr (NeXus attribute).

    Attributes:
    - nxclass (str): Class name of the NXattr.
    - value (Union[PrePostRunString, Scalar, ArrayLike]): Value of the
    attribute.
    - dtype (Optional[str]): Data type of the attribute.
    - shape (Optional[Union[list, Tuple[int]]]): Shape of the attribute if
    applicable.
    """

    nxclass: Optional[str] = Field("NXattr", description="The class of the NXattr.")
    value: Union[PrePostRunString, Scalar, ArrayLike] = Field(
        ..., description="Value of the attribute."
    )
    dtype: Optional[str] = Field(None, description="Data type of the attribute.")
    shape: Optional[Union[list, Tuple[int]]] = Field(
        None, description="Shape of the attribute."
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXFileModel(BaseModel):
    """NXFileModel.

    Pydantic model representing an NXFile (NeXus file structure).

    Attributes:
    - nxclass (str): Class name of the NXFile.
    - name (str): Name of the HDF5 file.
    - mode (str): Read/write mode.
    - recursive (Optional[bool]): Whether to load the file tree recursively.
    - kwargs (Dict[str, Any]): Additional keyword arguments for opening
        the file.
    """

    nxclass: str = Field("NXFile", description="The class of the NXFile.")
    name: str = Field(..., description="Name of the HDF5 file.")
    mode: str = Field("r", description="Read/write mode of the HDF5 file.")
    recursive: Optional[bool] = Field(
        None, description="If True, the file tree is loaded recursively."
    )
    kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments for opening the h5py file object.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXobjectModel(BaseModel):
    """NXobjectModel.

    Pydantic model representing a generic NXobject (NeXus object).

    Attributes:
    - nxclass (Optional[str]): Class name of the NXobject.
    - nxname (Optional[str]): Name of the NXobject.
    - nxpath (Optional[str]): Path of the object in the NeXus tree.
    - nxroot (Optional[NXgroupModel]): Root object of the NeXus tree.
    - nxfile (Optional[NXFileModel]): File handle of the root NeXus tree.
    - attrs (Optional[Dict[str, Any]]): Arbitrary user-defined attributes.
    """

    nxclass: Optional[str] = Field("NXobject", description="The class of the NXobject.")
    nx_model: Optional[str] = Field(None, description="The name of " "the model.")
    nxname: Optional[str] = Field(None, description="The name of the NXobject.")
    nxgroup: Optional["NXgroupModel"] = Field(
        None,
        description="The parent group containing this object within " "a NeXus tree.",
    )
    nxpath: Optional[str] = Field(
        None,
        description="The path to this object with respect to the root "
        "of the NeXus tree.",
    )
    nxroot: Optional["NXgroupModel"] = Field(
        None,
        description="The root object of the NeXus" " tree containing this " "object.",
    )
    nxfile: Optional["NXFileModel"] = Field(
        None,
        description="The file handle of the root object of the NeXus tree "
        "containing this object.",
    )
    nxfilename: Optional[str] = Field(
        None,
        description="The file name of NeXus object's " "tree file handle.",
    )
    attrs: Optional[Dict[str, Any]] = Field(
        default={},
        description="Arbitrary attributes belonging to a dataset assigned "
        "by a user.",
    )
    description: Optional[Any] = Field(
        None, description="Optional description of the object"
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXgroupModel(NXobjectModel):
    """NXgroupModel.

    Pydantic model representing an NXgroup (NeXus group).

    Inherits from NXobjectModel.
    """

    nxclass: str = Field(..., description="The class of the group.")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")


class TransformationModel(BaseModel):
    """TransformationModel.

    Pydantic model representing a symbolic transformation operation
    on a NeXus field.

    Attributes:
    - expression (str): Symbolic expression for transformation.
    - target (str): Target field for transformation.
    """

    expression: str = Field(
        ...,
        description="Symbolic expression that defines the transformation, "
        "using 'x' as the array variable. "
        "Examples: '3 * x**2 + 5', 'np.sqrt(x) + 2', np.log(x) + 3, "
        "np.exp(x) + 3",
    )
    target: str = Field(
        ...,
        description="Specifies the target array (e.g., 'value') on which "
        "the transformation is applied.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXfieldModel(NXobjectModel):
    """NXfieldModel.

    Pydantic model representing an NXfield (NeXus field object).

    Attributes:
    - value (Any): Value of the field.
    - dtype (Optional[str]): Data type of the field.
    """

    value: Any = Field(None, description="Value of the field.")
    dtype: Optional[str] = Field(None, description="Data type of the field.")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXfieldModelWithPrePostRunString(NXfieldModel):
    """NXfieldModelWithPrePostRunString.

    Extended NXfieldModel where the value must be a PrePostRunString.
    """

    nxclass: str = Field(..., description="The nexus class of the field.")
    value: PrePostRunString = Field(..., description="Value of the field.")
    dtype: Optional[str] = Field(None, description="Data type of the field.")
    transformation: Optional[TransformationModel] = Field(
        None,
        description="Transformation configuration that applies a symbolic "
        "operation to the target field.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class NXfieldModelForAttribute(NXfieldModel):
    """NXfieldModelForAttribute.

    Pydantic model representing an NXfield specifically for
    attributes.

    Attributes:
    - value (Union[PrePostRunString, str]): Value of the attribute field.
    """

    value: Union[PrePostRunString, Scalar, List[Scalar]] = Field(
        ..., description="Value of the attribute field."
    )
    dtype: Optional[str] = Field(None, description="Data type of the attribute field.")
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
