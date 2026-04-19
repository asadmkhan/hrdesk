from pathlib import Path
from typing import Literal

from pydantic import BaseModel

DocumentFormat = Literal["pdf", "txt", "md"]


class Document(BaseModel):
    source: Path
    format: DocumentFormat
    content: str


class Chunk(BaseModel):
    text: str
    source: Path
    chunk_index: int
    page: int | None = None
    heading: str | None = None
