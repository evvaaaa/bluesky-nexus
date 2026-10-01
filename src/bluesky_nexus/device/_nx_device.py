"""Contains a decorator for loading bluesky-nexus schema into a device's hints."""

from __future__ import annotations

from abc import ABC
from typing import Annotated, Any, TypeVar, cast, get_args, get_origin

from bluesky.protocols import HasHints, HasName
from ophyd import ClassVar

from bluesky_nexus.schema import NX_ATTRIBUTE_SERIALIZED_PREFIX, NxBaseClass

from ._bluesky_nexus_hints import NxHints
from .annotations import NxConstant, NxDataKey, NxSubGroup


def _get_nx_annotation_from_python_annotation(
    annotation: Any,
) -> NxDataKey | NxConstant | NxSubGroup | None:
    """Extracts the bluesky nexus annotation type from a single python type annotation."""
    candidates = get_args(annotation) if get_origin(annotation) is Annotated else (annotation,)

    for candidate in candidates:
        if isinstance(candidate, NxDataKey | NxConstant | NxSubGroup):
            return candidate

    return None


T = TypeVar("T")


class NxDevice(ABC):
    """A class which can be inherited from to provide schema to a device."""

    """The base class added via bluesky nexus.

    The decorator `NxDevice.insert_schema` embeds the schema instance here and patches
    the hints of the device.

    By inheriting `NxDevice`, and adding the `BLUESKY_NEXUS_BASE_CLASS` class variable to your
    subclass.
    """

    BLUESKY_NEXUS_BASE_CLASS: ClassVar[type[NxBaseClass] | NxBaseClass]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Enforce that subclasses define the class variable at runtime."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "BLUESKY_NEXUS_BASE_CLASS"):
            raise TypeError(
                f"{cls.__name__} must define class variable 'BLUESKY_NEXUS_BASE_CLASS'"
            )
        if not isinstance(cls, HasName):
            raise TypeError(
                "Can only inherit `NxDevice` on a device which corresponds to `HasName`."
            )
        if not isinstance(cls, HasHints):
            raise TypeError(
                "Can only inherit `NxDevice` on a device which corresponds to `HasHints`."
            )
        return None

    @property
    def hints(self) -> Any:  # Any because ophyd type hints this differently from ophyd async.
        """Hints from a device which inherits NxDevice.

        If a device inherits NxDevice then it specifies hints declaratively.
        """

        output = {}

        # The hints of this device if NxDevice weren't inherited, e.g
        # ophyd-async StandardReadable.hints.
        other_hints = None
        for parent_cls in type(self).mro()[1:]:
            if issubclass(parent_cls, NxDevice):
                continue

            if hasattr(parent_cls, "hints"):
                other_hints = parent_cls.hints
                break
        if other_hints is not None:
            output.update(other_hints.__get__(self))

        schema = self.nexus_schema()
        raw_schema = schema.model_dump(exclude_unset=True, exclude_none=True)

        output.update({"NX_class": schema.nxclass.constant, "NX_schema": raw_schema})

        return cast(NxHints, output)

    def nexus_schema(self: NxDevice) -> NxBaseClass:
        """Returns the schema instance specified for this device."""
        return _nexus_schema_from_nx_device(self, self.name)  # type: ignore


def _merged_annotations(obj: object) -> dict[str, type]:
    """Gives the annotations accross the MRO, including inherited."""
    cls = obj if isinstance(obj, type) else obj.__class__
    ann: dict[str, type] = {}
    for base in reversed(cls.mro()):  # base-first so subclass overrides
        ann.update(getattr(base, "__annotations__", {}))
    return ann


def _nexus_schema_from_nx_device(device: NxDevice, object_name: str) -> NxBaseClass:
    """Returns the bluesky-nexus schema for this NxDevice."""
    if isinstance(device.BLUESKY_NEXUS_BASE_CLASS, NxBaseClass):
        # Procedural definition requries no walking.
        return device.BLUESKY_NEXUS_BASE_CLASS

    schema_cls = device.BLUESKY_NEXUS_BASE_CLASS
    kwargs = {}

    # Declarative definition, parse the annotations.
    for name, annotation in _merged_annotations(device).items():
        nx_annotation = _get_nx_annotation_from_python_annotation(annotation)

        match nx_annotation:
            case NxConstant(nx_name=nx_name, is_nx_attribute=is_nx_attribute):
                # e.g - some_nexus_name: NxConstant(6)
                if not (constant_value := getattr(device, name, None)):
                    # Only append if the constant is defined on the instance.
                    continue

                if is_nx_attribute:
                    kwargs[f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}{nx_name}"] = constant_value
                else:
                    kwargs[nx_name] = {"constant": constant_value}
            case NxDataKey(nx_name=nx_name, is_nx_attribute=is_nx_attribute) if (
                signal := getattr(device, name, None)
            ) and isinstance(signal, HasName):
                # Remove the object name and the first separator from the datakey name.
                data_key_name = (
                    signal.name.removeprefix(object_name).removeprefix("-").removeprefix("_")
                )
                # e.g - some_data_key_name: NxConstant("the_name_in_nexus")
                if is_nx_attribute:
                    kwargs[f"{NX_ATTRIBUTE_SERIALIZED_PREFIX}{nx_annotation.nx_name}"] = {
                        "data_key": data_key_name
                    }
                else:
                    kwargs[nx_annotation.nx_name] = data_key_name

            # TODO: Declarative subdevices won't work in bluesky-nexus until
            # https://github.com/bluesky/ophyd-async/issues/1433
            # is resolved.
            # case NxSubGroup(nx_name=nx_name) if (
            #     sub_device := getattr(device, name, None)
            # ) and isinstance(sub_device, NxDevice):
            #     kwargs[nx_annotation.nx_name] = _nexus_schema_from_nx_device(
            #         sub_device, object_name
            #     )

    return schema_cls(**kwargs)  # type: ignore
