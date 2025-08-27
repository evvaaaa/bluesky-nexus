"""Module simulating a monochromator device.

.

This module defines a `Mono` device for Bluesky with NeXus schema support using Ophyd
components and includes a metadata simulation class `MetadataMono`.
The `Mono` class is decorated with a NeXus schema loader to allow structured
metadata integration.
"""

# pylint: disable=duplicate-code


from dataclasses import dataclass, field

from ophyd import Component as Cpt
from ophyd import Device, Signal
from ophyd.sim import SynAxis

from bluesky_nexus.common.decorator_utils import NxSchemaLoader

from .nx_schema.mono import Mono_nxschema


@dataclass
class MetadataMono:
    """Class simulating metadata for a monochromator.

    Attributes:
        grating_substrate_material (str): Material of the grating substrate.
        worldPosition (dict): Spatial position of the monochromator in 3D space.
        description (str): Description of the monochromator.
        calibration_on (bool): Flag indicating if calibration is enabled.
        baseline (str): Indicates if the device is part of the baseline.
        transformations_axisname (str): Name of the transformation axis.
    """

    grating_substrate_material: str = "lead"
    worldPosition: dict = field(  # pylint: disable=invalid-name
        default_factory=lambda: {
            "x": "1.2000000000000003",
            "y": "4.5000000000000006",
            "z": "7.8000000000000009",
        }
    )

    description: str = "I am the best mono at the bessyii facility"
    calibration_on: bool = True
    baseline: str = "True"
    transformations_axisname: str = "x"

    def get_attributes(self):
        """Return all metadata attributes of the monochromator.

        Returns:
            dict: A dictionary containing all metadata attributes.
        """
        attributes = {
            "grating_substrate_material": self.grating_substrate_material,
            "worldPosition": self.worldPosition,
            "description": self.description,
            "baseline": self.baseline,
            "calibration_on": self.calibration_on,
            "transformations_axisname": self.transformations_axisname,
        }
        return attributes


# Class simulating monochromator
@NxSchemaLoader(Mono_nxschema)
class Mono(Device):
    """Simulated monochromator device using Ophyd components.

    This class represents a monochromator with energy axis, grating and slit
    controls. The class is loaded with a NeXus schema for standardized metadata.

    Components:
        en (SynAxis): Simulated energy axis.
        grating (Signal): Simulated grating signal.
        slit (Signal): Simulated slit signal (marked as configuration).
        md (MetadataMono): Associated metadata for the monochromator.
    """

    en: SynAxis = Cpt(SynAxis, name="en")
    grating: Signal = Cpt(Signal, name="grating")
    slit: Signal = Cpt(Signal, name="slit", kind="config")
    md = MetadataMono()
