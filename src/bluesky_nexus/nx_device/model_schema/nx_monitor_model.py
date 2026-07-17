"""nx_monitor_model.

nx_monitor_model: Model for managing monitor-related metadata and
configuration.

This module defines a model that organizes and manages metadata and
configuration specific to monitors in an experimental setup. It includes
attributes to describe incident beam data, measurement times, monitor
efficiency, and transformations.

Classes:
    - NXmonitorModel: Model for managing monitor-related metadata and
    configuration.
"""

from typing import Optional

from .nx_core_models import (
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)
from .nx_log_model import NXlogModel
from .nx_off_geometry_model import NXoff_geometryModel
from .nx_transformations_model import (
    NXtransformationsModel,
)


class NXmonitorModel(NXgroupModel):
    """NXmonitorModel.

    Model for managing monitor-related metadata and configuration.

    This class organizes and manages metadata and configuration specific to
    monitors in an experimental setup. It allows for the inclusion of key
    attributes such as measurement times, monitor efficiency, and
    transformations.

    Attributes:
        default (Optional[NXfieldModelWithPrePostRunString]): Declares which
            child group contains a path leading to the default data to be
            plotted.
        mode (Optional[NXfieldModelWithPrePostRunString]): Count to a preset
            value based on either clock time (timer) or monitor counts
            (monitor).
        start_time (Optional[NXfieldModelWithPrePostRunString]): Starting time
            of measurement.
        end_time (Optional[NXfieldModelWithPrePostRunString]): Ending time of
            measurement.
        preset (Optional[NXfieldModelWithPrePostRunString]): Preset value for
            time or monitor.
        range (Optional[NXfieldModelWithPrePostRunString]): Range (X-axis,
            Time-of-flight, etc.) over which the integral was calculated.
        nominal (Optional[NXfieldModelWithPrePostRunString]): Nominal reading
            to be used for normalization purposes.
        integral (Optional[NXfieldModelWithPrePostRunString]): Total integral
            monitor counts.
        type (Optional[NXfieldModelWithPrePostRunString]): Type of monitor
            (e.g., Fission Chamber, Scintillator).
        time_of_flight (Optional[NXfieldModelWithPrePostRunString]):
            Time-of-flight data.
        efficiency (Optional[NXfieldModelWithPrePostRunString]): Monitor
            efficiency.
        data (Optional[NXfieldModelWithPrePostRunString]): Monitor data.
        sampled_fraction (Optional[NXfieldModelWithPrePostRunString]):
            Proportion of incident beam sampled by the monitor.
        count_time (Optional[NXfieldModelWithPrePostRunString]): Elapsed actual
            counting time.
        depends_on (Optional[NXfieldModelWithPrePostRunString]): Dependency
            chain for positioning the monitor.
        integral_log (Optional[NXlogModel]): Time variation of monitor counts.
        OFF_GEOMETRY (Optional[NXoff_geometryModel]): Shape of the beam line
            component.
        TRANSFORMATIONS (Optional[NXtransformationsModel]): Chain of
            translation and rotation operations necessary to position the
            component within the instrument.
    """

    default: NXattrModel = Field(NXattrModel(value="data"), description="Default.")
    mode: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Count to a preset value based on either clock time "
        "(timer) or monitor counts (monitor).",
    )
    start_time: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Starting time of measurement."
    )
    end_time: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Ending time of measurement."
    )
    preset: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Preset value for time or monitor."
    )
    range: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Range (X-axis, Time-of-flight, etc.) over which the "
        "integral was calculated.",
    )
    nominal: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Nominal reading to be used for normalization purposes.",
    )
    integral: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Total integral monitor counts."
    )
    type: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Type of monitor (e.g., Fission Chamber, Scintillator).",
    )
    time_of_flight: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Time-of-flight data."
    )
    efficiency: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Monitor efficiency."
    )
    data: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Monitor data."
    )
    sampled_fraction: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Proportion of incident beam sampled by the monitor."
    )
    count_time: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Elapsed actual counting time."
    )
    depends_on: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Dependency chain for positioning the monitor."
    )
    integral_log: Optional[NXlogModel] = Field(
        None, description="Time variation of monitor counts."
    )
    OFF_GEOMETRY: Optional[NXoff_geometryModel] = Field(
        None, description="Shape of the beam line component."
    )
    TRANSFORMATIONS: Optional[NXtransformationsModel] = Field(
        None,
        description="Chain of translation and rotation operations necessary "
        "to position the component within the instrument.",
    )
