"""Supplemental baseline preprocessor for Bluesky plans.

This module defines a custom subclass of `bluesky.preprocessors.SupplementalData`
that wraps a plan with a baseline measurement using `baseline_wrapper`.
"""

from bluesky.preprocessors import SupplementalData, baseline_wrapper


# Define preprocesor for the baseline
# pylint: disable=too-few-public-methods
class SupplementalDataBaseline(SupplementalData):
    """A supplemental data preprocessor.

    It adds baseline devices to a plan.

    This class extends `SupplementalData` to apply a baseline wrapper
    around a Bluesky plan, ensuring the specified baseline devices are
    read before and after plan execution.
    """

    def __init__(self, baseline, *args, **kwargs):
        """Initialize the preprocessor with baseline devices.

        Args:
            baseline (list): A list of Ophyd devices to include in the baseline.
            *args: Additional positional arguments passed to `SupplementalData`.
            **kwargs: Additional keyword arguments passed to `SupplementalData`.
        """
        super().__init__(*args, **kwargs)
        self.baseline = baseline

    def __call__(self, plan):
        """Wrap the plan with a baseline measurement.

        Args:
            plan (iterable): A Bluesky plan (a generator of Msgs).

        Returns:
            generator: The wrapped plan with baseline measurements added.
        """
        plan = baseline_wrapper(plan, self.baseline)
        return (yield from plan)
