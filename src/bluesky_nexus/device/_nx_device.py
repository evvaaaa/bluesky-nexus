from __future__ import annotations
from typing import Annotated, Generic, get_args, get_origin, Any
from typing import TYPE_CHECKING, Generic, TypeVar
from bluesky.protocols import HasHints

from ophyd import ClassVar, TypeVar

from .annotations import NxConstant, NxDataKey
from ._bluesky_nexus_hints import NxHints

"""Contains a decorator for loading bluesky-nexus schema into a device's hints."""

from typing import cast


from bluesky_nexus.schema import NxBaseClass


def _parse_annotations(device: NxDevice, schema: type[NxBaseClass]) -> NxBaseClass:
    kwargs = {}
    for name, annotation in type(device).__annotations__.items():
        nx_annotation = _get_nx_annotation(annotation)
        if isinstance(nx_annotation, NxConstant):
            # e.g - some_nexus_name: NxConstant(6)
            kwargs[name] = nx_annotation.constant
        elif isinstance(nx_annotation, NxDataKey):
            # e.g - some_data_key_name: NxConstant("the_name_in_nexus")
            kwargs[nx_annotation.nx_name] = name

    return schema(**kwargs)


def _get_nx_annotation(annotation: Any) -> NxDataKey | NxConstant | None:
    candidates = get_args(annotation) if get_origin(annotation) is Annotated else (annotation,)

    for candidate in candidates:
        if isinstance(candidate, NxDataKey | NxConstant):
            return candidate

    return None


def _sum_parent_schema[T](cls: type[T], schema_sofar: NxBaseClass) -> NxBaseClass:
    for direct_parent in cls.__bases__:
        schema_sofar += _sum_parent_schema(direct_parent, schema_sofar=schema_sofar)
        maybe_schema_instance = getattr(direct_parent, "BLUESKY_NEXUS_SCHEMA", None)
        if isinstance(maybe_schema_instance, NxBaseClass):
            schema_sofar += maybe_schema_instance

    return schema_sofar


def _get_other_hints(cls: type) -> property | None:
    """Gets the hints from the class which would have been defined if NxDevice had not been
    inherited, e.g ophyd-async StandardReadable.hints, or ophyd Device.hints."""
    mro = cls.mro()

    # Search the MRO (excluding the class itself) for the first 'hints' property
    # that is not defined on the generated per-parameterized NxDevice class.
    for base in mro[1:]:
        attr = base.__dict__.get("hints")
        if isinstance(attr, property):
            # Generated NxDevice classes created by __class_getitem__ put
            # BLUESKY_NEXUS_SCHEMA in their __dict__.  Skip those so we
            # return the hints from other parent classes.
            if "BLUESKY_NEXUS_SCHEMA" in base.__dict__:
                continue
            return attr
    return None


class _NxDeviceMeta(type):
    """Metaclass for generating a new NxDevice with __getitem__ instead of using generics."""

    def __getitem__(cls, schema: NxBaseClass | type[NxBaseClass]) -> type[NxDevice]:
        class _NxDevice:
            BLUESKY_NEXUS_SCHEMA: ClassVar[NxBaseClass | type[NxBaseClass]] = schema

            @property
            def hints(self) -> NxHints:
                """Appends the bluesky-nexus hints to the hints of the device
                which would be used if this class werent inherited."""

                output = {}

                # The hints of this device if NxDevice weren't inherited, e.g
                # ophyd-async StandardReadable.hints.
                other_hints = _get_other_hints(type(self))
                if other_hints is None:
                    raise TypeError(
                        "Inherited NxDevice in a class which doesn't contain hints "
                        "from other parent classes."
                    )
                output.update(other_hints.__get__(self))

                schema_or_schema_t = self.BLUESKY_NEXUS_SCHEMA

                if isinstance(schema_or_schema_t, type):
                    # Uisng declarative, parse the annotations.
                    schema = _parse_annotations(
                        self,  # type: ignore
                        schema_or_schema_t,
                    )
                else:
                    # Using procedural, sum the schema together.
                    schema = _sum_parent_schema(type(self), schema_or_schema_t)

                # schema_with_parents = _sum_parent_schema(type(self), schema)
                raw_schema = schema.model_dump(exclude_unset=True, exclude_none=True)
                output.update({"NX_class": schema.nxclass.constant, "NX_schema": raw_schema})

                return cast(NxHints, output)

        return _NxDevice  # type: ignore


class NxDevice(metaclass=_NxDeviceMeta):
    """A class which can be inherited from to provide schema to a device."""

    BLUESKY_NEXUS_SCHEMA: NxBaseClass
