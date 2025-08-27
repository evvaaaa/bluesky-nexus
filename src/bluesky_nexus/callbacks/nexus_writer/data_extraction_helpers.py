"""data_extraction_helpers.py.

Functions for retrieving and assembling component data from Bluesky descriptors
and events.

This module provides utilities for extracting measurement data and associated metadata
(such as timestamps and descriptions) from Bluesky document streams. It supports both
configuration-level (descriptor) and per-event data, handling both numeric and string
data types dynamically using NumPy arrays.

The logic includes a preference for non-baseline descriptors to prioritize primary
measurements.

Key Functions:
    - get_data_from_descriptor: Extracts component data and metadata from a descriptor's
      configuration section.
    - get_data_from_events: Gathers per-event data for a component from the event stream
      that matches a given descriptor.
    - extract_data: High-level helper that searches descriptors
    (preferring non-baseline) and extracts component data using the two methods above.

Dynamic typing and robust handling of strings, numbers, and lists are included
to support flexible and heterogeneous scientific datasets.

Logging:
    Uses the module logger to report debug information and missing data warnings.
"""

from typing import Deque, Optional

import numpy as np

from bluesky_nexus.common.logging_utils import logger


def get_data_from_descriptor(descriptor: dict, cpt_name: str) -> Optional[dict]:
    """Retrieve data from descriptor configuration."""
    config = descriptor.get("configuration", {})
    for _device_name, device_data in config.items():
        data_keys, data, timestamps = map(
            device_data.get, ["data_keys", "data", "timestamps"]
        )
        if data_keys and cpt_name in data_keys:
            logger.debug(
                "Data for component: '%s' found in configuration"
                " of descriptor: '%s'",
                cpt_name,
                descriptor["name"],
            )

            value = data.get(cpt_name)
            timestamp = timestamps.get(cpt_name)

            # Determine dtype dynamically for value
            if isinstance(value, (str, np.str_)):
                value_array = np.array(
                    value, dtype=object
                )  # Single string, keep object dtype
            elif isinstance(value, list):
                # Use object dtype if list contains any strings;
                # otherwise, let NumPy infer
                dtype = (
                    object
                    if any(isinstance(v, (str, np.str_)) for v in value)
                    else None
                )
                value_array = np.array(value, dtype=dtype)
            else:
                value_array = np.array(value)  # Let NumPy infer the best dtype

            # Determine dtype dynamically for timestamp
            if isinstance(timestamp, (str, np.str_)):
                timestamp_array = np.array(timestamp, dtype=object)
            elif isinstance(timestamp, list):
                # Use object dtype if list contains any strings;
                # otherwise, let NumPy infer
                dtype = (
                    object
                    if any(isinstance(t, (str, np.str_)) for t in timestamp)
                    else None
                )
                timestamp_array = np.array(timestamp, dtype=dtype)
            else:
                timestamp_array = np.array(timestamp)  # Let NumPy infer the best dtype

            return {
                "description": data_keys[cpt_name],
                "data": value_array,
                "descriptor_cpt_timestamp": timestamp_array,
            }
    return None


def get_data_from_events(descriptor: dict, events, cpt_name: str) -> Optional[dict]:
    """Retrieve data from events based on descriptor UID."""
    if cpt_name not in descriptor["data_keys"]:
        return None

    descriptor_uid = descriptor["uid"]
    filtered_events = [evt for evt in events if evt["descriptor"] == descriptor_uid]

    values: list = [
        evt["data"][cpt_name] for evt in filtered_events if cpt_name in evt["data"]
    ]
    timestamps: list = [
        evt["timestamps"][cpt_name]
        for evt in filtered_events
        if cpt_name in evt["timestamps"]
    ]
    event_times: list = [evt["time"] for evt in filtered_events]

    # Determine dtype dynamically for values
    if any(isinstance(v, (str, np.str_)) for v in values):
        values_array = np.array(values, dtype=object)  # Contains strings → use object
    else:
        values_array = np.array(values)  # Only numbers → NumPy infers dtype

    # Determine dtype dynamically for timestamps
    if any(isinstance(t, (str, np.str_)) for t in timestamps):
        timestamps_array = np.array(
            timestamps, dtype=object
        )  # Contains strings → use object
    else:
        timestamps_array = np.array(timestamps)  # Only numbers → NumPy infers dtype

    # Determine dtype dynamically for event_times
    if any(isinstance(t, (str, np.str_)) for t in event_times):
        event_times_array = np.array(
            event_times, dtype=object
        )  # Contains strings → use object
    else:
        event_times_array = np.array(event_times)  # Only numbers → NumPy infers dtype

    # Define data to be returned
    data: dict = {
        "description": descriptor["data_keys"][cpt_name],
        "data": values_array,
        "events_cpt_timestamps": timestamps_array,
        "events_timestamps": event_times_array,
    }
    logger.debug(
        "Data for component: '%s' found in %d event(s) of the descriptor: '%s'",
        cpt_name,
        len(data["data"]),
        descriptor["name"],
    )
    return data


def extract_data(descriptors: Deque, events: Deque, cpt_name: str) -> Optional[dict]:
    """extract_data.

    Extract data for cpt_name from descriptors, prioritizing non-
    baseline first.
    """

    def find_data(descriptor) -> Optional[dict]:
        return get_data_from_events(
            descriptor, events, cpt_name
        ) or get_data_from_descriptor(descriptor, cpt_name)

    # Prioritize non-baseline descriptors
    for descriptor in descriptors:
        if descriptor["name"] != "baseline":
            if data := find_data(descriptor):
                return data

    # Check baseline descriptor if no data found so far
    for descriptor in descriptors:
        if descriptor["name"] == "baseline":
            if data := find_data(descriptor):
                return data

    # No data found
    logger.warning(
        "No descriptor contains data for the 'cpt_name': %s",
        cpt_name,
    )
    return None
