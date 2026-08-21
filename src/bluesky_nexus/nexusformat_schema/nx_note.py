"""Contains the definition for NXnote."""

from typing import Self

from pydantic import model_validator

from bluesky_nexus.base_schema import (
    NxField,
    add_nx_class_basemodel,
)

from .nx_object import NxObject


@add_nx_class_basemodel
class NxNote(NxObject):
    """Represents a NeXus NXnote."""

    author: NxField | None = None
    """Author of this note."""

    date: NxField | None = None
    """Date of note creation."""

    type: NxField | None = None
    """Mime content type of note data field e.g. image/jpeg, text/plain, text/html"""

    file_name: NxField | None = None
    """Name of original file name if note was read from an external source."""

    checksum: NxField | None = None
    """Value of the hash that is obtained when running algorithm on the content of
    the resource referred to by identifierNAME."""

    algorithm: NxField | None = None
    """Name of the algorithm whereby the checksum was computed."""

    description: NxField | None = None
    """Title of an image or other details of the note."""

    sequence_index: NxField | None = None
    """Sequence index of note, for placing a sequence of multiple NXnote groups from some parent
    in an order. Starts with 1."""

    data: NxField | None = None
    """Binary note data - if text, line terminator is [CR][LF]."""

    @model_validator(mode="after")
    def _check_identifier(self) -> Self:
        for key, value in self:
            if key.startswith("identifier") and not isinstance(value, NxField):
                raise ValueError(f"{key} is an `identifierNAME` but not an NxField")
        return self
