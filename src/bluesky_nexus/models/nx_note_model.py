"""
Module: nx_note_model.

This module defines the `NXnoteModel` class, which represents a model for
storing and managing notes in the context of a Nexus data format. It is part
of the Bluesky Nexus implementation, which is designed to manage experimental
data and metadata in a structured and extensible way.

The `NXnoteModel` class is used to describe a note, which can contain textual
or binary data, and include metadata such as author, creation date, content
type, file name, description, and a sequence index for ordering multiple
notes.

Classes:
    NXnoteModel: A model that represents a note, containing attributes such as
                 author, date, type, description, sequence index, and binary
                 data.
"""

from typing import Optional

from bluesky_nexus.models.nx_core_models import (
    ConfigDict,
    Field,
    NXattrModel,
    NXfieldModelWithPrePostRunString,
    NXgroupModel,
)


class NXnoteModel(NXgroupModel):
    """NXnoteModel.

    Represents a note in the Nexus data format.

    It contains metadata and binary or textual data. It is designed to store
    information such as the author, creation date, MIME type, file name,
    description, sequence order and the note's content (either as text or
    binary data).

    This model is part of the Bluesky Nexus system, which is used to organize
    and manage experimental data. Each `NXnoteModel` instance can be associated
    with a specific note that may contain any form of data, including images,
    text, or other formats, along with relevant metadata.

    Attributes:
        default (NXattrModel): The default attribute, initially set to
        "author".
        author (Optional[NXfieldModelWithPrePostRunString]): The author or
            creator of the note.
        date (Optional[NXfieldModelWithPrePostRunString]): The date the note
        was created or added.
        type (Optional[NXfieldModelWithPrePostRunString]): The MIME type of the
            note data (e.g., "image/jpeg", "text/plain").
        file_name (Optional[NXfieldModelWithPrePostRunString]): The original
        file name if the note was read from an external file.
        description (Optional[NXfieldModelWithPrePostRunString]): A brief
            description or title of the note.
        sequence_index (Optional[NXfieldModelWithPrePostRunString]): The index
        of the note in a sequence of notes (starting from 1).
        data (Optional[NXfieldModelWithPrePostRunString]): The binary or
        textual data of the note.
        model_config (ConfigDict): Configuration settings for the model,
            allowing arbitrary types and forbidding extra fields.
    """

    default: NXattrModel = Field(NXattrModel(value="author"), description="Default")
    author: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Author or creator of note."
    )
    date: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Date note created/added."
    )
    type: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Mime content type of note data field e.g. image/jpeg, "
        "text/plain, text/html.",
    )
    file_name: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Name of original file name if note was read from an "
        "external source.",
    )
    description: Optional[NXfieldModelWithPrePostRunString] = Field(
        None, description="Title of an image or other details of the note."
    )
    sequence_index: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Sequence index of note, for placing a sequence of "
        "multiple NXnote groups in an order. Starts with 1.",
    )
    data: Optional[NXfieldModelWithPrePostRunString] = Field(
        None,
        description="Binary note data - if text, line terminator is [CR][LF].",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
