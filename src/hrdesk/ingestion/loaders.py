from collections.abc import Callable
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from hrdesk.domain.document import Document


def load_pdf(path: Path) -> Document:
    pages = PyPDFLoader(str(path)).load()
    page_text = [p.page_content for p in pages]
    content = "\n\n".join(page_text).strip()
    return Document(source=path, format="pdf", content=content)


def load_text(path: Path) -> Document:
    pages = TextLoader(str(path), encoding="utf-8").load()
    page_text = [p.page_content for p in pages]
    content = "\n\n".join(page_text).strip()
    return Document(source=path, format="txt", content=content)


def load_md(path: Path) -> Document:
    pages = TextLoader(str(path), encoding="utf-8").load()
    page_text = [p.page_content for p in pages]
    content = "\n\n".join(page_text).strip()
    return Document(source=path, format="md", content=content)


_LOADERS: dict[str, Callable[[Path], Document]] = {
    ".pdf": load_pdf,
    ".txt": load_text,
    ".md": load_md,
}


def load(path: Path) -> Document:
    suffix = path.suffix.lower()
    if suffix not in _LOADERS:
        raise ValueError(f"{suffix} is not supported")
    return _LOADERS[suffix](path)
