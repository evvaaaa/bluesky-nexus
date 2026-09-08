"""Tests specifically on NxData.

NxData has some complexity to allow function alongside NxLog fields.
"""

from pathlib import Path

import numpy as np
import pytest
from bluesky import RunEngine
from bluesky import plans as bp
from cycler import cycler
from numpy import sin
from ophyd_async.core import (
    StandardReadable,
    callback_on_mock_put,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from ophyd_async.plan_stubs import ensure_connected
from pydantic import ValidationError

from bluesky_nexus import NexusDevices
from bluesky_nexus.base_schema import NxAttribute, NxConstantAttribute, NxField, NxInternalLink
from bluesky_nexus.nexusformat_schema.nx_data import NxData

from . import load_only_generated_nexus_file


def test_nx_data_deserializes_with_links_and_serializes_without():
    dictionary_definition = {
        "$nxclass": "NXdata",
        "$axes": ["axis0", "axis1"],
        "$signal": "data",
        "data": "data-field",
        "axis0": "axis0-field",
        "axis1": "axis1-field",
        "$another_attribute": "another_attribute_value",
        "another_field": "another_field-field",
    }
    loaded = NxData.from_dictionary(dictionary_definition)
    assert loaded == NxData(
        axes=NxConstantAttribute(constant=["axis0", "axis1"]),
        signal=NxConstantAttribute(constant="data"),
        data=NxField(data_key="data-field"),
        axis0=NxField(data_key="axis0-field"),
        axis1=NxField(data_key="axis1-field"),
        another_attribute=NxAttribute(constant="another_attribute_value"),
        another_field=NxField(data_key="another_field-field"),
    )

    assert loaded.signal_link == NxInternalLink(link=["data"])
    assert loaded.axis0_link == NxInternalLink(link=["axis0"])
    assert loaded.axis1_link == NxInternalLink(link=["axis1"])
    assert loaded.axes == NxConstantAttribute(constant=["axis0_link", "axis1_link"])
    assert loaded.signal == NxConstantAttribute(constant="signal_link")
    assert loaded.axis0 == NxField(data_key="axis0-field")
    assert loaded.axis1 == NxField(data_key="axis1-field")
    assert loaded.data == NxField(data_key="data-field")
    assert loaded.another_attribute == NxAttribute(constant="another_attribute_value")
    assert loaded.another_field == NxField(data_key="another_field-field")

    assert loaded.model_dump() == dictionary_definition


def test_nx_data_multi_dimensional(RE_directly_subscribed: RunEngine, tmpdir: Path):
    @NexusDevices.add_device_from_schema(
        {
            "$nxclass": "NXdata",
            "$axes": ["some_axis1", "some_axis2"],
            "$signal": "some_signal",
            "some_signal": "another_signal",
            "some_axis1": "axis1",
            "some_axis2": "axis2",
        }
    )
    class MultiAxisDataDetector(StandardReadable):
        def __init__(self, name: str = ""):
            super().__init__(name=name)
            with self.add_children_as_readables():
                self.additional_signal, self._setter = soft_signal_r_and_setter(float)
                self.axis1 = soft_signal_rw(float)
                self.axis2 = soft_signal_rw(float)
                self.another_signal, _ = soft_signal_r_and_setter(int)

        async def _new_value(self, *args, **kwargs):
            self._setter(sin(await self.axis1.get_value()) * sin(await self.axis2.get_value()))

        async def connect(self, *args, **kawrgs):
            await super().connect(mock=True)
            callback_on_mock_put(self.axis1, self._new_value)
            callback_on_mock_put(self.axis2, self._new_value)

    detector = MultiAxisDataDetector(name="some_detector")
    RE_directly_subscribed(ensure_connected(detector))
    RE_directly_subscribed(
        bp.scan_nd(
            [detector],
            cycler(detector.axis1, range(5)) * cycler(detector.axis2, range(10)),
        )
    )
    loaded = load_only_generated_nexus_file(tmpdir)["entry"]["primary"]["devices"]["some_detector"]
    assert list(loaded) == [
        "additional_signal",
        "axis0_link",
        "axis1_link",
        "signal_link",
        "some_axis1",
        "some_axis2",
        "some_signal",
    ]
    assert set(loaded.attrs) == {"axes", "nxclass", "signal"}
    assert loaded.attrs["nxclass"] == "NXdata"
    assert loaded.attrs["signal"] == "signal_link"
    assert loaded.attrs["axes"] == ["axis0_link", "axis1_link"]
    assert list(loaded[loaded.attrs["axes"][0]]) == (
        ([np.float64(0.0)] * 10)
        + ([np.float64(1.0)] * 10)
        + ([np.float64(2.0)] * 10)
        + ([np.float64(3.0)] * 10)
        + ([np.float64(4.0)] * 10)
    )
    assert list(loaded[loaded.attrs["axes"][1]]) == [np.float64(i) for i in range(10)] * 5
    assert list(loaded[loaded.attrs["signal"]]) == list(np.zeros(50))

    assert loaded[loaded.attrs["signal"]].attrs["long_name"] == "some_signal"


@pytest.mark.parametrize(
    ("specification", "exception_cls", "exception_text"),
    [
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
            },
            ValidationError,
            "axes\n  Field required",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$axes": ["axis_signal_1"],
            },
            ValidationError,
            "signal\n  Field required",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", 2],
            },
            ValidationError,
            "Input should be a valid string [type=string_type, input_value=2, input_type=int]",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": "some_axis_name",
            },
            TypeError,
            "Received single string {'axes': {'constant': 'some_axis_name'}}, this "
            "should be an iterable of string.",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", "axis_signal_2"],
            },
            TypeError,
            "Referenced signal `some_signal_name` is not an NxField inside `NxData`",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": "some_signal_name",
                "$axes": ["axis_signal_1", "axis_signal_2"],
                "some_signal_name": "some_data_key",
            },
            TypeError,
            "Referenced axis `axis_signal_1` is not an NxField inside `NxData`",
        ),
        (
            {
                "$nxclass": "NXdata",
                "$signal": {"data_key": "some_data_key"},
                "$axes": ["axis_signal_1", "axis_signal_2"],
                "some_signal_name": "signal",
                "some_axis_name_1": "axis_signal_1",
                "some_axis_name_2": "axis_signal_2",
            },
            ValidationError,
            "signal.data_key\n  Input should be None",
        ),
    ],
)
def test_nx_data_incorrect_specification(
    specification: dict, exception_cls: type[Exception], exception_text: str
):
    with pytest.raises(exception_cls) as excinfo:
        NxData.from_dictionary(specification)

    assert exception_text in str(excinfo)
