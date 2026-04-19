from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

from hrdesk.domain.document import Chunk
from hrdesk.retrieval._lc_conversion import from_langchain_document, to_langchain_document
from hrdesk.retrieval.vector_store import get_vector_store

_ensemble: EnsembleRetriever | None = None


def build_index(chunks: list[Chunk]) -> None:
    global _ensemble
    lc_docs = [to_langchain_document(c) for c in chunks]

    bm25 = BM25Retriever.from_documents(lc_docs)
    bm25.k = 5

    vector = get_vector_store().as_retriever(search_kwargs={"k": 5})

    _ensemble = EnsembleRetriever(
        retrievers=[bm25, vector],
        weights=[0.5, 0.5],
    )


def search(query: str, k: int = 5) -> list[Chunk]:
    if _ensemble is None:
        raise RuntimeError("Hybrid index not built. Call build_index() first.")
    lc_docs = _ensemble.invoke(query)
    return [from_langchain_document(d) for d in lc_docs[:k]]
