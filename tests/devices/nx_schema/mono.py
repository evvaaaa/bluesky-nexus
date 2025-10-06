"""
Module: mono.py.

This module contains the YAML schema definition in form of a yml string for
the monochromator, which is used for storing and processing data in the Nexus format.
"""

# Mono_nxschema: YAML Schema for Mono
# ===================================

Mono_nxschema: str = """
nx_model: NXmonochromatorModel # pydantic model associated with this schema
nxclass: NXmonochromator # group: NXmonochromator

energy: # field: "energy" belongs to NXmonochromator group
  nxclass: NX_FLOAT
  value: $post-run:en # fetch it from the device component
  dtype: float64
  attrs: # attrs belong to field: "energy"
    units: "keV"
    prices: "Euro"
    days: ["Mo", "We"]
    factors: [1.34, 2.78]
    destination: { "departement": "A23" }
    value: 12.34
    PI: 3.1415
    active: [True, False]
  transformation:
    expression: 3 * x**2 + np.exp(np.log(5)) + 1
    # symbolic expression for the transformation
    target: value # specifies the name of array to which expression is applied
GRATING: # group: 'GRATING' belongs to NXmonochromator group
  nxclass: NXgrating
  attrs: # attrs belong to group "GRATING"
    attr_0: "new"
    value: 167
  diffraction_order: # field: "diffraction_order" belongs to group "GRATING"
    nxclass: NX_INT
    value: $pre-run-cpt:grating
    dtype: int32
    attrs: # attrs belong to field "diffraction_order"
      at_0: 13.14
      at_1: [2.03, 4.05]
      value: "some_value"
TRANSFORMATIONS: # group: 'TRANSFORMATIONS' belongs to NXmonochromator group
  nxclass: NXtransformations
  attrs: # attrs belong to group "TRANSFORMATIONS"
    attr_0: 3.1415
    value: "3.1"
    attr_1: { "a": "2" }
    attr_2: [1.01, 2.02]
  alpha: # field: 'alpha' belongs to group "TRANSFORMATIONS"
    nxclass: NX_CHAR
    value: $pre-run-md:transformations_axisname
    # fetch it from the device metadata (happi)
    dtype: str
    attrs: # attrs belong to field "AXISNAME"
      units: "um"
      value: 123
    attributes: # attributes of the AXISNAME
      vector: # obligatory attribute of the AXISNAME
        value: [0, 1, 0]
        dtype: int64
      offset: # facultative attribute of the AXISNAME
        value: 34.56
        dtype: float64
      offset_units: # facultative attribute of the AXISNAME
        value: "um"
        dtype: str
      depends_on: # facultative attribute of the AXISNAME
        value: $pre-run-md:transformations_axisname
        # fetch it from the device metadata (happi)
        dtype: str
      equipment_component: # facultative attribute of "AXISNAME"
        value: "A.71"
        dtype: str
  alpha_end: # field: 'AXISNAME_end' belongs to group "TRANSFORMATIONS"
    nxclass: NX_FLOAT
    value: $post-run:en
    dtype: float64
  alpha_increment_set: # field: 'AXISNAME_increment_set' of group "TRANSFORMATIONS"
    nxclass: NX_INT
    value: $post-run:en
    dtype: int32
description: # field: 'description' belongs to NXmonochromator group
  nxclass: NX_CHAR
  value: $pre-run-md:description # fetch it from the device metadata (happi)
  dtype: str
attrs: # attrs belong to NXmonochromator group
  attr_0: 3.1415
  value: "3.1415"
  attr_1: { "a": "2" }
  attr_2: "{'b':'1'}"
  attr_3: [1.02, 3.04, 5.06]
  attr_4: [5, 6, 7]
  attr_5: True

###
### NXmonochromator group allows extra groups/fields that are not explicitly
### defined in the model
###
someGroup: # additional group: "someGroup"
  nxclass: NXsomeClass
  attrs:
    attr_1: { "a": "2" }
    attr_2: [5.06, 7.08]
  energy: # field energy belonging to someGroup
    nxclass: NX_FLOAT
    value: $post-run:en
    dtype: float64
    attrs:
      attr_1: "PI"
      attr_2: 3.1415
someDataset: # additional dataset: "someDataset"
  nxclass: NX_FLOAT
  value: $post-run:en
  dtype: float64
"""


# The following is a nxschema that does not participate in any of the tests.
# This schema can be used to start debugging the creation of the group attributes.
# This is a test of the creation:
# - A group with 6 attributes
# If you want to run it:
# - Rename in devices/monochromators/mono.py the parameter passed to decorator from
#   "Mono_nxschema" to "Mono1_nxschema"
# - Execute test_2 only (in debug mode) with the deactivated function
#   verify_nexus_file()

# Mono1_nxschema: YAML Schema for Mono1
# ====================================================

Mono1_nxschema: str = """
nx_model: NXgeneralModel # pydantic model associated with this schema
nxclass: NXmonochromator # group: NXmonochromator

TRANSFORMATIONS: # group: 'TRANSFORMATIONS' belongs to NXmonochromator group
  nxclass: NXtransformations
  attributes: # attributes of the AXISNAME
    at_0: # facultative attribute of the group TRANSFORMATIONS
      value: $post-run:en # fetch it from the device component
      #dtype: int8
    at_1: # facultative attribute of the group TRANSFORMATIONS
      value: $pre-run-md:transformations_axisname
      dtype: str
    at_2: # facultative attribute of the group TRANSFORMATIONS
      value: ["I am", "string"]
      dtype: str
    at_3: # facultative attribute of the group TRANSFORMATIONS
      value: 3.1415
      dtype: float32
    at_4: # facultative attribute of the group TRANSFORMATIONS
      value: 14
      dtype: int32
    at_5: # facultative attribute of the group TRANSFORMATIONS
      value: True
      dtype: bool
"""
