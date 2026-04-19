from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from hrdesk.agent import agent
from hrdesk.config import settings
from hrdesk.ingestion.pipeline import ingest_directory
from hrdesk.observability.logging import configure_logging, get_logger
from hrdesk.retrieval import hybrid
from hrdesk.retrieval.vector_store import index_chunks

log = get_logger(__name__)

_INDEX_HTML = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


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


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    log.info("chat_request", question=req.question)
    answer_text = agent.answer(req.question)
    log.info("chat_response", question=req.question, answer=answer_text)
    return ChatResponse(answer=answer_text)
