# Mock HR Service

FastAPI app that pretends to be the HR backend. HRDesk's vacation tool calls
it over HTTP.

## Run

From this directory:

```
uv run uvicorn main:app --port 8001 --reload
```

First run sets up its own venv and installs FastAPI + uvicorn.

## Endpoints

- `GET /health` → `{"status": "ok"}`
- `GET /employees/{id}/vacation` → vacation balance
- `GET /docs` → Swagger UI

## Seeded employees

| ID | Name | Days remaining |
|---|---|---|
| E001 | Asad Khan | 18 |
| E002 | Marcel Heling | 11 |
| E003 | Priya Sharma | 3 |

## Why separate

Real HR systems (Workday, SAP, ServiceNow) are separate processes behind HTTP.
Building the mock the same way means swapping to a real API is a base URL
change, not a rewrite.
