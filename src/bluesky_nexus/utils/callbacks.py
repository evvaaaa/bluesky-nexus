"""callbacks.py — Debugging callbacks for Bluesky document streams.

This module is not used operationally in the `bluesky_nexus` package.
It is only used in tests. It is intended purely as a debugging and development aid.

It defines three callback classes that subscribe to Bluesky's RunEngine
and handle documents (e.g., 'start', 'event', 'stop') in different ways
for inspection or offline storage.

Classes:
    WriteToFileCallback:
        Writes Bluesky documents as newline-delimited JSON objects (one per line),
        suitable for streaming or large-scale logging.

    WriteToFileFormattedCallback:
        Collects all Bluesky documents and writes them at once as a formatted
        JSON array, making it more readable for humans.

    WriteToTerminalCallback:
        Prints Bluesky documents to the terminal in a human-readable format
        using `pprint`, useful for real-time inspection.

Usage:
    These callbacks can be passed to the `RunEngine.subscribe()` method
    to process and debug document streams during Bluesky runs.

Example:
    from bluesky import RunEngine
    from bluesky.plans import count
    from ophyd.sim import det
    from bluesky_nexus.aux.callbacks import (
        WriteToFileCallback,
        WriteToFileFormattedCallback,
        WriteToTerminalCallback
    )

    RE = RunEngine({})

    # Example 1: Write documents as JSON lines
    with WriteToFileCallback("stream_output.json") as file_callback:
        RE.subscribe(file_callback)
        RE(count([det], num=5))

    # Example 2: Write all documents as a pretty-printed JSON array
    with WriteToFileFormattedCallback("formatted_output.json") as formatted_callback:
        RE.subscribe(formatted_callback)
        RE(count([det], num=5))

    # Example 3: Print documents to the terminal
    terminal_callback = WriteToTerminalCallback()
    RE.subscribe(terminal_callback)
    RE(count([det], num=5))

Notes:
    - `WriteToFileCallback` is suitable for large, streaming data.
    - `WriteToFileFormattedCallback` is ideal for compact, human-readable snapshots.
    - `WriteToTerminalCallback` is best for real-time debugging output.
"""

import json
from pprint import pprint

from bluesky.callbacks import CallbackBase


class WriteToFileCallback:
    """WriteToFileCallback.

    A context manager and callable class for writing JSON-formatted
    name-documentation pairs to a file, one per line.

    This class opens the specified file on entering the context and ensures the file
    is properly closed on exit. It can be called like a function to write a dictionary
    entry to the file in JSON format.

    Attributes:
        file_path (str): Path to the file where data will be written.
        file (file object): File handle used for writing.
    """

    def __init__(self, file_path):
        """Initialize the WriteToFileCallback with the path to the file.

        Args:
            file_path (str): The path to the file where entries will be written.
        """
        self.file_path = file_path
        self.file = None

    def __enter__(self):
        """Enter the runtime context related to the file resource.

        Returns:
            WriteToFileCallback: The instance itself, with the file opened.
        """
        self.file = open(self.file_path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and close the file if it was opened.

        Args:
            exc_type (type): Exception type, if raised.
            exc_value (Exception): Exception value, if raised.
            traceback (traceback): Traceback object, if an exception was raised.
        """
        if self.file:
            self.file.close()

    def __call__(self, name, doc):
        """Write a JSON-formatted line.

        to the file with a name-documentation pair.

        Args:
            name (str): The key name for the documentation entry.
            doc (str): The documentation content to associate with the name.
        """
        self.file.write(json.dumps({name: doc}) + "\n")
        self.file.flush()


class WriteToFileFormattedCallback:
    """WriteToFileFormattedCallback.

    A callback class that collects all documents and writes them to a
    file as a single pretty-printed JSON array.

    Useful for cases where you want a more human-readable, structured
    output instead of streaming line-by-line.
    """

    def __init__(self, file_path):
        """Initialize the WriteToFileFormattedCallback.

        Parameters:
        ----------
        file_path : str
            Path to the file where the formatted JSON output will be written.
        """
        self.file_path = file_path
        self.file = None
        self.documents = []

    def __enter__(self):
        """Open the file on entering the context."""
        self.file = open(self.file_path, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Write documents and close the file on exiting the context."""
        json.dump(self.documents, self.file, indent=4)
        self.file.flush()

    def __call__(self, name, doc):
        """Collect a document for later formatted output.

        Parameters:
        ----------
        name : str
            The name/type of the document (e.g., 'start', 'event', 'stop').
        doc : dict
            The document content to be collected.
        """
        self.documents.append({name: doc})


class WriteToTerminalCallback(CallbackBase):
    """WriteToTerminalCallback.

    A callback class that prints streaming documents to the terminal in
    a human-readable format.

    Each type of document (start, descriptor, event, stop) is printed
    with a header and content. Useful for debugging and development to
    inspect live data.
    """

    def start(self, doc):
        """Handle the 'start' document.

        Parameters:
        ----------
        doc : dict
            The start document containing metadata about the run.
        """
        print("/n# I got a new 'start' document:/n")
        pprint(doc)

    def descriptor(self, doc):
        """Handle the 'descriptor' document.

        Parameters:
        ----------
        doc : dict
            The descriptor document describing the data schema for subsequent events.
        """
        print("/n# I got a new 'descriptor' document:/n")
        pprint(doc)

    def event(self, doc):
        """Handle an 'event' document.

        Parameters:
        ----------
        doc : dict
            The event document containing measured data.
        """
        print("/n# I got a new 'event' document:/n")
        pprint(doc)

    def stop(self, doc):
        """Handle the 'stop' document.

        Parameters:
        ----------
        doc : dict
            The stop document signaling the end of a run.
        """
        print("/n# I got a new 'stop' document:/n")
        pprint(doc)
