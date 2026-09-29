from pathlib import Path

from bluesky import RunEngine
from bluesky import plans as bp
from ophyd_async.sim import SimPointDetector

from bluesky_nexus import NxDevice
from bluesky_nexus.schema import NxBaseClass

from . import (
    load_only_generated_nexus_file,
)


def test_internal_device_links(RE_directly_subscribed: RunEngine, tmpdir: Path) -> None:
    dictionary = {
        "$nxclass": "NXcomponent",
        "channel_1_value": "channel-1-value",
        "channel_3_value": "channel-3-value",
        "&link_in_parent": ["channel_1_value"],
        "sub_group": {
            "$nxclass": "NXcomponent",
            "&link_parent_outside_sub_group": ["channel_3_value"],
            "channel_2_value": "channel-2-value",
        },
        "&link_sub_group_outside_sub_group": ["sub_group", "channel_2_value"],
        "&link_to_subgroup": ["sub_group"],
    }

    class SimPointDetectorWithSchema(
        NxDevice[NxBaseClass.from_dictionary(dictionary)], SimPointDetector
    ):
        pass

    RE_directly_subscribed(
        bp.count(
            [
                SimPointDetectorWithSchema(None, name="sim_point_detector_with_schema"),
            ],
            num=3,
        )
    )

    loaded = load_only_generated_nexus_file(tmpdir)
    device = loaded["entry"]["primary"]["devices"]["sim_point_detector_with_schema"]
    assert list(device) == [
        "channel_1_mode",
        "channel_1_value",
        "channel_2_mode",
        "channel_3_mode",
        "channel_3_value",
        "link_in_parent",
        "link_sub_group_outside_sub_group",
        "link_to_subgroup",
        "sub_group",
    ]

    assert list(device["sub_group"]) == ["channel_2_value", "link_parent_outside_sub_group"]

    assert (
        device["sub_group"]["link_parent_outside_sub_group"].nxtarget
        == "/entry/primary/devices/sim_point_detector_with_schema/channel_3_value/value"
    )
    assert list(loaded[device["sub_group"]["link_parent_outside_sub_group"].nxtarget]) == [
        290,
        290,
        290,
    ]

    assert (
        device["link_in_parent"].nxtarget
        == "/entry/primary/devices/sim_point_detector_with_schema/channel_1_value/value"
    )
    assert list(loaded[device["link_in_parent"].nxtarget]) == [
        290,
        290,
        290,
    ]

    assert (
        device["link_sub_group_outside_sub_group"].nxtarget
        == "/entry/primary/devices/sim_point_detector_with_schema/sub_group/channel_2_value/value"
    )
    assert list(loaded[device["link_sub_group_outside_sub_group"].nxtarget]) == [
        290,
        290,
        290,
    ]

    assert (
        device["link_to_subgroup"].nxtarget
        == "/entry/primary/devices/sim_point_detector_with_schema/sub_group"
    )
    assert list(loaded[device["link_to_subgroup"].nxtarget]) == [
        "channel_2_value",
        "link_parent_outside_sub_group",
    ]


# TODO: see comment in comment above `NxGroup._check_nx_links_reference_real_fields_and_subgroups`
# @pytest.mark.parametrize(
#     ("schema", "error"),
#     [
#         (
#             {"$nxclass": "NXsubentry", "&non_existant": ["non_existant_field"]},
#             "Malformed link specified, the link does not map to a defined field in the schema",
#         ),
#         (
#             {
#                 "$nxclass": "NXsubentry",
#                 "&non_existant": ["sub_group", "sub_group_non_existent"],
#                 "sub_group": {"$nxclass": "NXobject"},
#             },
#             "Malformed link specified, the link does not map to a defined field in the schema:",
#         ),
#         (
#             {
#                 "$nxclass": "NXsubentry",
#                 "&self_referencing": ["self_referencing"],
#             },
#             "Malformed link specified, the link does not map to an NxField or NxGroup, "
#             "instead :\n",
#         ),
#         (
#             {
#                 "$nxclass": "NXsubentry",
#                 "$attribute": "foo",
#                 "&attribute_link": ["attribute"],
#             },
#             "Malformed link specified, the link does not map to an NxField or NxGroup, "
#             "instead :\n",
#         ),
#     ],
# )
# def test_internal_device_links_error_in_specification(schema: dict, error: str):
#     with pytest.raises(
#         TypeError,
#         match=error,
#     ):
#
#         @NxDevice.add_device_from_dictionary(schema)
#         class SimPointDetectorWithSchema(SimPointDetector): ...
