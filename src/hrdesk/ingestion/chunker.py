from langchain_text_splitters import RecursiveCharacterTextSplitter

from hrdesk.domain.document import Chunk, Document

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def chunk_document(document: Document) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    pieces = splitter.split_text(document.content)

    return [
        Chunk(text=piece, source=document.source, chunk_index=i) for i, piece in enumerate(pieces)
    ]
