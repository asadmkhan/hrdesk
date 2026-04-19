# Evals

Quick test harness for the agent. 25 questions in `golden.jsonl`, runs them through
the agent, checks three things:

- route picked by the classifier
- whether the right source doc showed up in the top-3 retrieval
- whether the final answer contains the expected keywords

Keyword matching is intentionally dumb. Good enough to spot regressions when tuning
prompts or swapping models.

## Run

HR service needs to be up on 8001 for tool cases. Then:

```
uv run python evals/run_evals.py
```

Per-case JSONL lands in `evals/results/` (gitignored).

## Golden set

One JSON object per line in `golden.jsonl`. Fields:

- `id` — short identifier
- `question` — user input
- `route` — expected route (CAN_ANSWER / CALL_EXTERNAL_TOOL / NO_MATCH)
- `source` — expected source filename, CAN_ANSWER only
- `must_contain` — keywords the answer must contain (case-insensitive)

Add a case = one new line.

## When scores drop

- routing fails: fix the classifier prompt
- retrieval misses: chunk size or ensemble weights
- answer wrong but retrieval right: the answer prompt, or try a bigger model
