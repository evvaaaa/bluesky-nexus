"""Contains the definition for NXdetector."""


from pydantic import Field

from bluesky_nexus.nx_schema import (
    NxAttribute,
    NxField,
    add_nx_class_basemodel,
)
from bluesky_nexus.nx_schema._nx_attribute import NxConstantAttribute

from .nx_component import NxComponent
from .nx_data import NxData
from .nx_log import NxTimeField
from .nx_note import NxNote


class NxEfficiency(NxData):
    wavelength_indices: NxAttribute | None = None
    """Obligatory value: 0"""

    efficiency: NxField
    """Efficiency of the detector."""

    signal: NxConstantAttribute[str] = Field(
        default_factory=lambda: NxConstantAttribute(constant="efficiency"),
    )
    """Has to be `efficiency`."""

    wavelength: NxField | None = None
    """Either, for a pixel detector it provides the nominal wavelength for which the detector has
    been calibrated, or for other detectors seen together with the efficiency field above."""


class NxRawTimeOfFlightField(NxField):
    frequency: NxAttribute | None = None
    """Clock frequency in Hz."""


class NxFieldWithLocalName(NxField):
    local_name: NxAttribute | None = None
    """Equivalent local term."""


@add_nx_class_basemodel
class NxDetector(NxComponent):
    """Represents a NeXus NXdetector.

    Additional fields of NXcollection and NXdetector_module are expected.
    """

    data: NxField
    """Data values from the detector. The rank and dimension ordering should follow
    a principle of slowest to fastest measurement axes and may be explicitly specified
    in application definitions."""

    time_of_flight: NxField | None = None
    """Total time of flight."""

    raw_time_of_flight: NxRawTimeOfFlightField | None = None
    """In DAQ clock pulses"""

    detector_number: NxField | None = None
    """Identifier for detector (pixels) Can be multidimensional, if needed."""

    data_errors: NxField | None = None
    """The best estimate of the uncertainty in the data value (array size should match the data
    field). Where possible, this should be the standard deviation, which has the same units
    as the data. The form data_error is deprecated."""

    x_pixel_offset: NxField | None = None
    """Offset from the detector center in x-direction. Can be multidimensional when needed."""

    y_pixel_offset: NxField | None = None
    """Offset from the detector center in y-direction. Can be multidimensional when needed."""

    z_pixel_offset: NxField | None = None
    """Offset from the detector center in z-direction. Can be multidimensional when needed."""

    description: NxField | None = None
    """Name/manufacturer/model/etc. information."""

    serial_number: NxField | None = None
    """Serial number for the detector."""

    local_name: NxField | None = None
    """Local name for the detector."""

    solid_angle: NxField | None = None
    """Solid angle subtended by the detector at the sample."""

    x_pixel_size: NxField | None = None
    """Size of each detector pixel. If it is scalar all pixels are the same size."""

    y_pixel_size: NxField | None = None
    """Size of each detector pixel. If it is scalar all pixels are the same size."""

    dead_time: NxField | None = None
    """Detector dead time."""

    gas_pressure: NxField | None = None
    """Detector gas pressure."""

    detection_gas_path: NxField | None = None
    """Maximum drift space dimension."""

    crate: NxFieldWithLocalName | None = None
    """Crate number of detector."""

    slot: NxFieldWithLocalName | None = None
    """Slot number of detector."""

    input: NxFieldWithLocalName | None = None
    """Input number of detector."""

    type: NxField | None = None
    """Description of type such as He3 gas cylinder, He3 PSD, scintillator, fission chamber,
    proportion counter, ion chamber, ccd, pixel, image plate, CMOS, ."""

    real_time: NxField | None = None
    """Real-time of the exposure (use this if exposure time varies for
    each array element, otherwise use count_time field)."""

    start_time: NxTimeField | None = None
    """Start time for each frame, with the start attribute as absolute reference."""

    stop_time: NxTimeField | None = None
    """Stop time for each frame, with the start attribute as absolute reference."""

    calibration_date: NxField | None = None
    """Date of last calibration (geometry and/or efficiency) measurements."""

    layout: NxField | None = None
    """How the detector is represented. Any of these values: point | linear | area."""

    count_time: NxField | None = None
    """Elapsed actual counting time."""

    # Sequence number purposfully ommited.

    beam_center_x: NxField | None = None
    """This is the x position where the direct beam would hit the detector. This is a length and
    can be outside of the actual detector. The length can be in physical units or pixels
    as documented by the units attribute."""

    beam_center_y: NxField | None = None
    """This is the y position where the direct beam would hit the detector. This is a length and
    can be outside of the actual detector. The length can be in physical units or pixels
    as documented by the units attribute."""

    frame_start_number: NxField | None = None
    """This is the start number of the first frame of a scan. In protein crystallography
    measurements one often scans a couple of frames on a give sample, then does something else,
    then returns to the same sample and scans some more frames. Each time with a new data file.
    This number helps concatenating such measurements."""

    diameter: NxField | None = None
    """The diameter of a cylindrical detector."""

    acquisition_mode: NxField | None = None
    """The acquisition mode of the detector. One of gated | triggered | summed | event |
       histogrammed | decimated | pulse counting."""

    angular_calibration_applied: NxField | None = None
    """True when the angular calibration has been applied in the electronics, false otherwise."""

    angular_calibration: NxField | None = None
    """Angular calibration data."""

    flatfield_applied: NxField | None = None
    """True when the flat field correction has been applied in the electronics, false otherwise."""

    flatfield: NxField | None = None
    """Flat field correction data."""

    flatfield_errors: NxField | None = None
    """Errors of the flat field correction data. The form flatfield_error is deprecated."""

    pixel_mask_applied: NxField | None = None
    """True when the pixel mask correction has been applied in the electronics, false otherwise."""

    pixel_mask: NxField | None = None
    """The 32-bit pixel mask for the detector. Can be either one mask for the whole dataset
    (i.e. an array with indices i, j) or each frame can have its own mask
    (in which case it would be an array with indices np, i, j)."""

    image_key: NxField | None = None
    """This field allow to distinguish different types of exposure to the same detector “data”
    field. Some techniques require frequent (re-)calibration inbetween measurements and this
    way of recording the different measurements preserves the chronological order with is
    important for correct processing."""

    countrate_correction_applied: NxField | None = None
    """Counting detectors usually are not able to measure all incoming particles,
    especially at higher count-rates. Count-rate correction is applied to account
    for these errors."""

    countrate_correction_lookup_table: NxField | None = None
    """The countrate_correction_lookup_table defines the LUT used for count-rate correction."""

    virtual_pixel_interpolation_applied: NxField | None = None
    """True when virtual pixel interpolation has been applied, false otherwise."""

    bit_depth_readout: NxField | None = None
    """How many bits the electronics reads per pixel. With CCD’s and single photon counting
    detectors, this must not align with traditional integer
    sizes. This can be 4, 8, 12, 14, 16, ..."""

    detector_readout_time: NxField | None = None
    """Time it takes to read the detector (typically milliseconds). This is
    important to know for time resolved experiments."""

    trigger_delay_time: NxField | None = None
    """Time it takes to start exposure after a trigger signal has been received."""

    trigger_delay_time_set: NxField | None = None
    """User-specified trigger delay."""

    trigger_internal_delay_time: NxField | None = None
    """Time it takes to start exposure after a trigger signal has been received."""

    trigger_dead_time: NxField | None = None
    """Time during which no new trigger signal can be accepted. Typically this is the
    trigger_delay_time + exposure_time + readout_time. This is important to know
    for time resolved experiments."""

    frame_time: NxField | None = None
    """This is time for each frame. This is exposure_time + readout time."""

    gain_setting: NxField | None = None
    """The gain setting of the detector. This is a detector-specific value meant to document the
    gain setting of the detector during data collection, for detectors with multiple available
    gain settings."""

    saturation_value: NxField | None = None
    """The value at which the detector goes into saturation. Especially common to CCD detectors,
    the data is known to be invalid above this value."""

    underload_value: NxField | None = None
    """The lowest value at which pixels for this detector would be reasonably measured.
    The data is known to be invalid below this value."""

    number_of_cycles: NxField | None = None
    """CCD images are sometimes constructed by summing together multiple short exposures in
    the electronics. This reduces background etc. This is the number of short exposures used to
    sum images for an image."""

    sensor_material: NxField | None = None
    """At times, radiation is not directly sensed by the detector. Rather, the detector might
    sense the output from some converter like a scintillator. This is the
    name of this converter material."""

    sensor_thickness: NxField | None = None
    """At times, radiation is not directly sensed by the detector. Rather, the detector might
    sense the output from some converter like a scintillator. This is the thickness
    of this converter material."""

    threshold_energy: NxField | None = None
    """Single photon counter detectors can be adjusted for a certain energy range in which they
    work optimally. This is the energy setting for this."""

    depends_on: NxField | None = None
    """The reference point of the detector is the center of the first pixel. In complex geometries
    the NXoff_geometry groups can be used to provide an unambiguous reference."""

    # CHANNELNAME_channel TODO

    efficiency: NxData | None = None
    """Spectral efficiency of detector with respect to e.g. wavelength."""

    calibration_method: NxNote | None = None
    """Summary of conversion of array data to pixels (e.g. polynomial approximations)
    and location of details of the calibrations."""

    data_file: NxNote | None = None
    """File the detector writers to."""
