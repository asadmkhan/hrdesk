# Mock HR Service

A tiny standalone FastAPI service simulating a company HR system.
HRDesk's vacation-lookup tool calls this over HTTP.

## Run

From this directory:

```
uv run uvicorn main:app --port 8001 --reload
```

First run sets up the virtualenv and installs FastAPI + uvicorn (~30 seconds).

## Endpoints

- `GET /health` — `{"status": "ok"}`
- `GET /employees/{employee_id}/vacation` — vacation balance
- `GET /docs` — FastAPI-generated Swagger UI

## Seeded employees

| ID | Name | Days remaining |
|---|---|---|
| E001 | Asad Khan | 18 |
| E002 | Marcel Heling | 11 |
| E003 | Priya Sharma | 3 |

## Why a separate service

This is intentionally a standalone FastAPI app with its own `pyproject.toml`, not
a function inside HRDesk. It mirrors reality: HR systems like Workday, SAP, or
ServiceNow live in separate processes with their own deployment lifecycles.
HRDesk's vacation tool calls it via HTTP — the same way it would call a real
enterprise HR API in production. Swapping the mock for a real API is changing
the base URL in HRDesk's config; no code changes to the agent.
