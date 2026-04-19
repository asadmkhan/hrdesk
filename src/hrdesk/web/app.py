from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from hrdesk.agent import agent
from hrdesk.config import LLMProvider, settings
from hrdesk.ingestion.pipeline import ingest_directory
from hrdesk.observability.logging import configure_logging, get_logger
from hrdesk.providers.factory import available_providers
from hrdesk.retrieval import hybrid
from hrdesk.retrieval.vector_store import index_chunks

log = get_logger(__name__)

_INDEX_HTML = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")


class ChatRequest(BaseModel):
    question: str
    provider: LLMProvider | None = None


class ChatResponse(BaseModel):
    answer: str
    provider: str


class ProvidersResponse(BaseModel):
    default: str | None
    available: list[str]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    log.info("web_starting", provider=settings.llm_provider)
    chunks = ingest_directory(settings.data_dir)
    index_chunks(chunks)
    hybrid.build_index(chunks)
    log.info("web_ready", chunks=len(chunks))
    yield


app = FastAPI(title="HRDesk", version="0.1.0", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@app.get("/api/providers", response_model=ProvidersResponse)
def providers() -> ProvidersResponse:
    available = [p.value for p in available_providers()]
    default = settings.llm_provider.value if settings.llm_provider.value in available else None
    if default is None and available:
        default = available[0]
    return ProvidersResponse(default=default, available=available)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    chosen = req.provider or settings.llm_provider
    log.info("chat_request", question=req.question, provider=chosen)

    try:
        answer_text = agent.answer(req.question, provider_override=req.provider)
    except Exception as e:
        log.error("chat_failed", provider=chosen, error=str(e))
        answer_text = _friendly_error(chosen, e)

    log.info("chat_response", question=req.question, answer=answer_text)
    return ChatResponse(answer=answer_text, provider=chosen.value)


def _friendly_error(provider: LLMProvider, error: Exception) -> str:
    if provider == LLMProvider.OLLAMA:
        return (
            "I could not reach the local Ollama service. Make sure Ollama is running "
            "and the configured model is pulled, or switch to Anthropic in the Model "
            "dropdown."
        )
    if provider == LLMProvider.ANTHROPIC:
        return (
            "The Anthropic provider is not configured correctly. Set ANTHROPIC_API_KEY "
            "in your .env file, or switch to Ollama in the Model dropdown."
        )
    return f"The {provider.value} provider failed: {error}"
