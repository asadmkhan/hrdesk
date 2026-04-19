# HRDesk

RAG chatbot for HR questions. Answers policy stuff from company docs, looks up
personal data (vacation balance) from a mock HR service.

Take-home project.

## What it does

Three types of questions, three code paths:

- policy question (e.g. "what's the dress code?") → retrieve from docs, cite source
- personal data ("how many vacation days do I have left?") → call the HR service
- off-topic ("what's the weather?") → canned refusal, no LLM call

A small classifier picks the path on every turn.

## Run

You need three things running: an LLM provider (Ollama or Anthropic), the mock HR
service, and the web app.

### Ollama

```
ollama pull llama3.2:3b
```

On Windows it runs as a tray service, no extra step. Use `qwen2.5:7b` instead
if you have GPU + 8GB VRAM, it's noticeably better.

### Mock HR service

Separate FastAPI app, own pyproject. In its own terminal:

```
cd external/hr_service
uv run uvicorn main:app --port 8001
```

Leave it running.

### Web app

In a fresh terminal at the project root:

```
uv sync
uv run hrdesk
```

First run downloads the embedding model (~90MB) and builds the vector index.
Takes about a minute.

Open http://127.0.0.1:8000. Top-right dropdown lets you switch between Ollama
and Anthropic per request — only providers that are actually working show up.

### Anthropic instead of Ollama

Copy `.env.example` to `.env`, set:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Same pipeline, different backend.

## Architecture

```
Browser ──▶ HRDesk web (:8000) ──▶ Ollama / Anthropic
               │
               └──▶ Mock HR service (:8001)
```

Per-question flow:

```
question
  ↓
classify
  ├─ CAN_ANSWER          → hybrid search + LLM with context
  ├─ CALL_EXTERNAL_TOOL  → pick tool + args → run → LLM with result
  └─ NO_MATCH            → hardcoded refusal
```

## Layout

```
src/hrdesk/
├── config.py        .env-driven settings
├── domain/          Document, Chunk, Message
├── providers/       Anthropic + Ollama adapters
├── ingestion/       loaders, chunker, pipeline
├── retrieval/       chroma + bm25 + hybrid
├── tools/           tool protocol + registry + vacation tool
├── agent/           prompts + 3-way routing
├── observability/   structlog
└── web/             FastAPI + chat HTML

external/hr_service/   separate mock service
data/                  sample HR docs
evals/                 test harness + golden set
```

## Notes on design

**LangChain.** Used it for loaders, splitter, vector store, retrievers, and
LLM clients. LlamaIndex was the other option but its tool model assumes
in-process, which clashes with the HTTP HR service. Writing everything from
scratch wasn't realistic in the time I had.

**Hybrid retrieval.** BM25 + dense vectors with reciprocal rank fusion.
`EnsembleRetriever` from `langchain-classic`, 50/50 weights. Vectors miss
rare keywords, BM25 misses paraphrases, the combo handles both.

**Mock HR is a real FastAPI service.** Not a dict. Runs on its own port
with its own dependencies. Closer to how a real integration with Workday
or SAP would look — you'd change a base URL, not rewrite.

**Classifier-first routing.** One cheap LLM call picks the route. Works
uniformly across providers, which native tool-calling doesn't. NO_MATCH
short-circuits without a second LLM call.

**Providers behind a Protocol.** Anthropic and Ollama both implement
`ChatProvider`. A factory picks which one per request. The UI has a
dropdown but under the hood it's a one-line config change.

**Domain types at the edge.** `Chunk` and `Message` are mine. LangChain's
types never leave `retrieval/` and `providers/`, they're converted at
the boundary.

## Evals

See `evals/README.md`. 25 golden questions, measures routing accuracy,
retrieval hit@3, and answer correctness. Run:

```
uv run python evals/run_evals.py
```

Current scores vary by provider and model. Numbers from my runs are in
the detailed JSONL output under `evals/results/`.

## Things I'd add

- conversation history (each turn is independent right now)
- auth — `CURRENT_EMPLOYEE_ID` is hardcoded to `E001` for the demo
- SSE streaming — answers currently arrive in one chunk
- unit tests on the translators and dispatchers
- incremental ingestion instead of full reindex on startup
- page numbers preserved through the PDF loader for tighter citations
- markdown-aware chunking
- retry/backoff on HR API calls
- prompt injection guards on user input

## Stack

Python 3.12, uv, FastAPI, LangChain (community / classic / chroma / huggingface /
text-splitters / anthropic / ollama), ChromaDB, BGE-small-en-v1.5 embeddings,
structlog, pydantic + pydantic-settings, Ruff.
