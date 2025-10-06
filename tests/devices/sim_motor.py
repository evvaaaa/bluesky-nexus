"""Simulation module for a motor with metadata.

This module defines a simulated motor and its associated metadata for
use in testing and development with the Bluesky and Ophyd frameworks.
"""

# pylint: disable=duplicate-code

from dataclasses import dataclass, field

from ophyd.sim import motor1  # pylint: disable=no-name-in-module


# Class simulating metadata of SimMotor
@dataclass
class MetadataSimMotor:
    """Simulated metadata for a motor.

    Provides static metadata attributes such as world position,
    description, and baseline status.
    """

    worldPosition: dict = field(  # pylint: disable=invalid-name
        default_factory=lambda: {
            "x": "1.2000000000000003",
            "y": "4.5000000000000006",
            "z": "7.8000000000000009",
        }
    )

    description: str = "I am a simulated motor"
    baseline: bool = True

    def get_attributes(self):
        """Return the metadata attributes as a dictionary.

        Returns:
            dict: A dictionary containing world position, description,
                  and baseline status.
        """
        attributes = {
            "worldPosition": self.worldPosition,
            "description": self.description,
            "baseline": self.baseline,
        }
        return attributes


# pylint: disable=too-few-public-methods
class SimMotor(motor1.__class__):  # or simply: class SimMotor(type(motor)):
    """A simulated motor with attached metadata.

    Inherits from the class of the `ophyd.sim.motor` instance to replicate
    the motor interface for testing purposes. Attaches a `MetadataSimMotor`
    instance as `self.md`.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the simulated motor.

        Args:
            *args: Positional arguments passed to the base motor class.
            **kwargs: Keyword arguments passed to the base motor class.

        The instance also attaches a simulated metadata object (`self.md`)
        that provides static attributes such as position, description, and
        baseline status.
        """
        super().__init__(*args, **kwargs)
        self.md = MetadataSimMotor()
