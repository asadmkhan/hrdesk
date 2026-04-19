from langchain_chroma import Chroma

from hrdesk.config import settings
from hrdesk.domain.document import Chunk
from hrdesk.observability.logging import get_logger
from hrdesk.retrieval._lc_conversion import from_langchain_document, to_langchain_document
from hrdesk.retrieval.embedder import get_embedder

log = get_logger(__name__)

COLLECTION_NAME = "hrdesk_chunks"


def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedder(),
        persist_directory=str(settings.chroma_dir),
    )


def index_chunks(chunks: list[Chunk]) -> None:
    if not chunks:
        log.warning("no_chunks_to_index")
        return

    store = get_vector_store()
    lc_docs = [to_langchain_document(c) for c in chunks]
    store.add_documents(lc_docs)
    log.info("chunks_indexed", count=len(chunks))


def search(query: str, k: int = 5) -> list[Chunk]:
    store = get_vector_store()
    lc_docs = store.similarity_search(query, k=k)
    return [from_langchain_document(d) for d in lc_docs]
