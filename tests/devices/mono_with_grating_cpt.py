"""Simulated monochromator device with grating and associated metadata.

This module defines a simulated monochromator device (`MonoWithGratingCpt`)
that includes a grating component, an energy axis, and a slit signal. It also
defines metadata through the `MetadataMonoWithGratingCpt` class and a subcomponent
`Grating`. This simulation setup is intended for testing and NeXus schema integration.
"""

# pylint: disable=duplicate-code

from dataclasses import dataclass, field

from ophyd import Component as Cpt
from ophyd import Device, Signal
from ophyd.sim import SynAxis

from bluesky_nexus.common.decorator_utils import NxSchemaLoader

from .nx_schema.mono_with_grating_cpt import MonoWithGratingCpt_nxschema


@dataclass
class MetadataMonoWithGratingCpt:
    """Simulated metadata for a monochromator with a grating component.

    Attributes:
        grating_substrate_material (str): Material used in the grating substrate.
        worldPosition (dict): Dictionary of x, y, z spatial coordinates.
        description (str): Human-readable description of the device.
        baseline (str): Indicates if the device is part of the experimental baseline.
    """

    grating_substrate_material: str = "leadless"

    worldPosition: dict = field(  # pylint: disable=invalid-name
        default_factory=lambda: {
            "x": "11.120000013",
            "y": "14.150000016",
            "z": "17.180000019",
        }
    )

    description: str = "I am the best mono with grating cpt at the bessyii facility"
    baseline: str = "True"

    def get_attributes(self):
        """Return the metadata attributes as a dictionary.

        Returns:
            dict: Metadata attributes for the monochromator.
        """
        attributes = {
            "grating_substrate_material": self.grating_substrate_material,
            "worldPosition": self.worldPosition,
            "description": self.description,
            "baseline": self.baseline,
        }
        return attributes


# Class simulating grating component of monochromator
class Grating(Device):
    """Simulated grating component with a diffraction order signal.

    Components:
        diffraction_order (Signal): Represents the diffraction order setting
        of the grating.
    """

    diffraction_order: Signal = Cpt(Signal, name="diff_order")


# Class simulating monochromator with grating component
@NxSchemaLoader(MonoWithGratingCpt_nxschema)
class MonoWithGratingCpt(Device):
    """Simulated monochromator device.

    This class simulates a monochromator setup with an energy axis, grating component,
    and a slit signal. It is decorated with a NeXus schema loader for
    structured metadata.

    Components:
        grating (Grating): Simulated grating subcomponent.
        engry (SynAxis): Simulated energy axis of the monochromator.
        slit (Signal): Simulated slit width or position signal.
        md (MetadataMonoWithGratingCpt): Metadata associated with the device.
    """

    grating: Grating = Cpt(Grating, name="grating")
    engry: SynAxis = Cpt(SynAxis, name="engry")
    slit: Signal = Cpt(Signal, name="slit")
    md = MetadataMonoWithGratingCpt()
