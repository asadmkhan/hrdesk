# HRDesk

A RAG chatbot for HR questions. It answers policy questions from company
documents and looks up personal HR data (like vacation balance) from a live
HR service.

Built as a take-home assignment. The architecture is close to what I would
use in production.

## What it does

Three kinds of questions, three different routes:

**Policy question** — *"What is the dress code?"*
Retrieves the relevant chunks from the HR documents, answers with a citation.

**Personal data question** — *"How many vacation days do I have left?"*
Calls the mock HR service over HTTP, phrases the result naturally.

**Off-topic question** — *"What's the weather?"*
Returns a polite refusal. No LLM call, no tokens spent.

An LLM classifier picks the route on every turn.

## Running it

You need three things up: Ollama (or an Anthropic key), the mock HR service,
and HRDesk itself.

### 1. Ollama

Install Ollama, then pull a small model:

```
ollama pull llama3.2:3b
```

On Windows, Ollama runs as a background service — nothing else to start.

### 2. Mock HR service

This is a separate FastAPI app that simulates a real HR system like Workday.
It lives in `external/hr_service/` with its own `pyproject.toml`.

```
cd external/hr_service
uv run uvicorn main:app --port 8001
```

Leave this running.

### 3. HRDesk

In a fresh terminal at the project root:

```
uv sync
uv run hrdesk
```

First run takes a minute — uv installs deps, the embedding model downloads
(~90MB), Chroma builds the vector index.

Open http://127.0.0.1:8000 in a browser. You'll see a chat UI with example
questions you can click.

### Using Anthropic instead of Ollama

Copy `.env.example` to `.env` and set:

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

No code changes. Swapping providers is the whole point of the adapter layer.

## Architecture

```
Browser ──▶ HRDesk web app ──▶ Ollama / Anthropic
               │
               └──▶ Mock HR service (FastAPI, :8001)
```

Inside HRDesk, each question flows through:

```
question
   ↓
classify (LLM)
   ├─ CAN_ANSWER          → hybrid search → LLM with context → answer
   ├─ CALL_EXTERNAL_TOOL  → pick tool + args → run → LLM with result → answer
   └─ NO_MATCH            → canned refusal (no LLM call)
```

## Project layout

```
src/hrdesk/
├── config.py        settings loaded from .env
├── domain/          Document, Chunk, Message, ToolCall
├── providers/       LLM adapters (Anthropic, Ollama) behind one Protocol
├── ingestion/       load → chunk → emit
├── retrieval/       vector + BM25 + hybrid (reciprocal rank fusion)
├── tools/           tool definitions + registry
├── agent/           prompts, classifier, answer generation
├── observability/   structlog setup
└── web/             FastAPI app + minimal HTML chat UI

external/hr_service/   standalone mock service (FastAPI on port 8001)
data/                  sample HR documents (PDF, TXT, Markdown)
```

## Design decisions

**LangChain for the pipeline.** Loaders, splitter, vector store, retrievers,
LLM clients — all LangChain. I looked at LlamaIndex (its in-process tool
model fights my FastAPI-based HR service) and writing the whole pipeline
myself (too expensive for three days). LangChain won on breadth and time to
working system. The trade-off is less deep ownership of the retrieval
algorithms — I can still explain what each piece does.

**Hybrid retrieval.** Dense vectors match meaning; BM25 matches exact terms.
Either alone leaves gaps — vectors miss rare keywords, BM25 misses
paraphrases. Reciprocal rank fusion merges the two. `EnsembleRetriever` from
`langchain-classic` does the merge with a 50/50 weight.

**Mock HR as a real FastAPI service, not a Python dict.** Real HR systems
(Workday, SAP, ServiceNow) live in separate processes behind HTTP. Modeling
that boundary now means swapping for a real API is a base-URL change, not a
rewrite.

**Three-way classifier routing.** Every turn starts with an LLM call that
returns `CAN_ANSWER`, `CALL_EXTERNAL_TOOL`, or `NO_MATCH`. The NO_MATCH path
is a hardcoded reply — no LLM call for refusals. Saves tokens, gives
consistent wording.

**Two LLM providers behind one Protocol.** Anthropic for quality, Ollama for
"runs with no API key." Swapping is a `.env` change; agent code doesn't
know which backend it's talking to.

**Domain types at the edge.** `Chunk` and `Message` are my own pydantic
models. LangChain's `Document` and message classes never leave `retrieval/`
or `providers/`. If I swap LangChain tomorrow, only those folders change.

**Prompts in their own file.** Non-code content, iterated separately from
agent logic. No inline prompt strings scattered across the codebase.

## What I'd add with more time

- **Evaluation harness.** A golden Q/A set with retrieval hit@k, routing
  accuracy, and answer correctness. This is the biggest quality lever and
  the next thing I would build.
- **Conversation history.** Each turn is independent right now. Real chat
  needs session memory.
- **Authenticated user identity.** `CURRENT_EMPLOYEE_ID` is hardcoded to
  `"E001"` for the demo. In production this comes from the session.
- **Streaming.** Answers arrive all at once; streaming tokens via SSE would
  make the UI feel faster.
- **Unit tests** on the translator functions and dispatcher helpers.
- **Incremental ingestion.** I re-index everything on startup. Real systems
  hash files and skip unchanged ones.
- **Page numbers in citations.** LangChain's PDF page metadata gets dropped
  at the loader boundary; preserving it would tighten citations.
- **Markdown-aware chunking** via `MarkdownHeaderTextSplitter` to preserve
  section context.
- **Retry with backoff** on HR API calls.
- **Input filtering** against prompt injection — user text flows straight
  into the LLM right now.

## Stack

Python 3.12, uv for packages, FastAPI for the web layer, LangChain
(community + classic + chroma + huggingface + text-splitters + anthropic +
ollama), ChromaDB for vectors, BGE-small-en-v1.5 for embeddings (local, no
API key), structlog for logging, pydantic for settings and domain types,
Ruff for lint/format.
