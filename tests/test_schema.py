from pydantic import ValidationError
import pytest

from bluesky_nexus.schema.nx_base_class import BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY, NxBaseClass


def test_nx_transformations():
    # Allowed
    NxBaseClass.from_dictionary({"$nxclass": "NXtransformations"})
    NxBaseClass.from_dictionary({"$nxclass": "NXtransformations", "$some_attribute": "Some Attr"})
    NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXtransformations",
            "some_field": {"data_key": "some_data_key", "$vector": (1, 0, 0)},
        }
    )

    NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXtransformations",
            "some_field": {"data_key": "some_data_key", "$vector": (1, 0, 0)},
            "some_field_end": "some_data_key",
        }
    )

    with pytest.raises(TypeError):
        # Trying to make a field for an attribute
        NxBaseClass.from_dictionary(
            {
                "$nxclass": "NXtransformations",
                "some_field": {"data_key": "some_data_key", "vector": "some_data_key"},
            }
        )


def test_schema_addition() -> None:
    nx_sub_entry = NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXsubentry",
            "$nx_sub_entry_hints_attribute_not_overwritten": {
                "hints_key": "nx_sub_entry_hints_key"
            },
            "$nx_sub_entry_constant_attribute_not_overwritten": "nx_sub_entry_constant",
            "$nx_sub_entry_constant_attribute": "nx_sub_entry_constant",
            "$nx_sub_entry_hints_attribute": {"hints_key": "nx_sub_entry_hints_attribute"},
            "SUB_GROUP": {
                "$nxclass": "NXsubentry",
                "field1": {
                    "data_key": "nx_sub_entry_data_key1",
                    "$attribute11": "nx_sub_entry_attribute11",
                },
                "field3": {
                    "data_key": "nx_sub_entry_data_key3",
                    "$attribute31": "nx_sub_entry_attribute13",
                },
            },
            "field2": {
                "data_key": "nx_sub_entry_data_key2",
                "$attribute21": "nx_sub_entry_attribute21",
                "$attribute22": "nx_sub_entry_attribute22",
            },
        }
    )
    nx_object = NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXobject",
            "$nx_object_constant_attribute": "nx_object_constant",
            "$nx_sub_entry_hints_attribute_not_overwritten": {"hints_key": "nx_object_hints_key"},
            "$nx_sub_entry_constant_attribute_not_overwritten": "nx_object_constant",
            "SUB_GROUP": {
                "$nxclass": "NXobject",
                "field1": {
                    "data_key": "nx_object_data_key1",
                    "$attribute11": "nx_object_attribute11",
                    "$attribute12": "nx_object_attribute12",
                },
                "field2": {
                    "data_key": "nx_object_data_key2",
                    "$attribute21": "nx_object_attribute21",
                },
            },
            "field2": {
                "data_key": "nx_object_data_key2",
                "$attribute21": "nx_object_attribute21",
                "$attribute22": "nx_object_attribute22",
            },
        }
    )

    assert (nx_sub_entry + nx_object).model_dump() == {
        "$nxclass": "NXsubentry",
        "$nx_object_constant_attribute": "nx_object_constant",
        "$nx_sub_entry_constant_attribute": "nx_sub_entry_constant",
        "$nx_sub_entry_constant_attribute_not_overwritten": "nx_sub_entry_constant",
        "$nx_sub_entry_hints_attribute": {"hints_key": "nx_sub_entry_hints_attribute"},
        "$nx_sub_entry_hints_attribute_not_overwritten": {"hints_key": "nx_sub_entry_hints_key"},
        "SUB_GROUP": {
            "$nxclass": "NXsubentry",
            "field1": {
                "$attribute11": "nx_sub_entry_attribute11",
                "data_key": "nx_sub_entry_data_key1",
            },
            "field2": {"$attribute21": "nx_object_attribute21", "data_key": "nx_object_data_key2"},
            "field3": {
                "$attribute31": "nx_sub_entry_attribute13",
                "data_key": "nx_sub_entry_data_key3",
            },
        },
        "field2": {
            "$attribute21": "nx_sub_entry_attribute21",
            "$attribute22": "nx_sub_entry_attribute22",
            "data_key": "nx_sub_entry_data_key2",
        },
    }
    # nx_sub_entry can not be added to nx_object because it's not a subclass of it.
    assert (nx_object + nx_sub_entry).model_dump() == nx_object.model_dump()


def test_attempt_with_unknown_schema_from_client() -> None:
    with pytest.raises(
        FileNotFoundError,
        match=(
            rf"(?:\[Errno \d+\] )?No such file or directory: "
            rf"['\"]?{str(BLUESKY_NEXUS_BASE_CLASSES_DIRECTORY).replace('.', r'\.')}"
            rf"/NXbanana\.nxdl\.xml['\"]?"
        ),
    ):
        NxBaseClass.from_dictionary({"$nxclass": "NXbanana", "length": "length"})


def test_writer_behaviour_failing_to_match_schema() -> None:
    with pytest.raises(
        TypeError,
        match=(
            "Malformed attribute/field found in nx schema. One method of obtaining "
            "the attribute value should be provided:"
        ),
    ):
        NxBaseClass.from_dictionary(
            {
                "$nxclass": "NXdetector",
                "data": {
                    "$nxclass": "NXsubentry",
                    "second_data_level_that_shouldnt_exist": {
                        "data_key": "channel-1-mode",
                    },
                },
            }
        )


def test_loading_schema_from_a_non_existent_path() -> None:
    with pytest.raises(
        ValueError, match=r"Path `/.*/tests/some_sub_package/my_schema.yaml` does not exist\."
    ):  # Becomes absolute, includin root.
        NxBaseClass.from_path("some_sub_package/my_schema.yaml")


def test_acceptable_nx_data_specification():
    NxBaseClass.from_dictionary(
        {
            "$nxclass": "NXdata",
            "$signal": "some_signal_name",
            "$axes": ["some_axis_name_1", "some_axis_name_2"],
            "some_signal_name": "signal",
            "some_axis_name_1": "axis_signal_1",
            "some_axis_name_2": "axis_signal_2",
        }
    )


def test_nxdl_schema_enforces_required_fields(use_test_nxdl_path):
    NxWithRequiredField = NxBaseClass.build("NXwith_required_field")
    with pytest.raises(ValidationError, match="required_field\n  Field required"):
        NxWithRequiredField()
