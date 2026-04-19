from pathlib import Path

from langchain_core.documents import Document as LCDocument

from hrdesk.domain.document import Chunk


def to_langchain_document(chunk: Chunk) -> LCDocument:
    return LCDocument(
        page_content=chunk.text,
        metadata={
            "source": str(chunk.source),
            "chunk_index": chunk.chunk_index,
            "page": chunk.page if chunk.page is not None else -1,
            "heading": chunk.heading or "",
        },
    )


def from_langchain_document(doc: LCDocument) -> Chunk:
    page = doc.metadata.get("page", -1)
    heading = doc.metadata.get("heading", "")
    return Chunk(
        text=doc.page_content,
        source=Path(doc.metadata["source"]),
        chunk_index=doc.metadata["chunk_index"],
        page=page if page != -1 else None,
        heading=heading or None,
    )
