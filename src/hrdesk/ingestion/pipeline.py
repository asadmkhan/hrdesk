from pathlib import Path

from hrdesk.domain.document import Chunk
from hrdesk.ingestion.chunker import chunk_document
from hrdesk.ingestion.loaders import load
from hrdesk.observability.logging import get_logger

log = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def ingest_directory(data_dir: Path) -> list[Chunk]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    all_chunks: list[Chunk] = []
    files = [p for p in data_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]

    log.info("ingestion_starting", file_count=len(files), data_dir=str(data_dir))

    for file_path in files:
        document = load(file_path)
        chunks = chunk_document(document)
        all_chunks.extend(chunks)

        log.info(
            "file_ingested",
            file=file_path.name,
            format=document.format,
            chars=len(document.content),
            chunks=len(chunks),
        )

    log.info("ingestion_complete", total_chunks=len(all_chunks))
    return all_chunks
