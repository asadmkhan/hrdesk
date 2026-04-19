"""Evaluation harness for HRDesk.

Reads evals/golden.jsonl, runs each question through the agent, and reports:
  - Routing accuracy   (did the classifier pick the expected route?)
  - Retrieval hit@3    (did the expected source appear in the top-3 chunks?)
  - Answer correctness (does the final answer contain all required keywords?)

Run from project root:
    uv run python evals/run_evals.py
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from hrdesk.agent import agent
from hrdesk.config import settings
from hrdesk.ingestion.pipeline import ingest_directory
from hrdesk.retrieval import hybrid
from hrdesk.retrieval.vector_store import index_chunks

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"


@dataclass
class Case:
    id: str
    question: str
    route: str
    source: str | None = None
    must_contain: list[str] = field(default_factory=list)


@dataclass
class Result:
    case: Case
    actual_route: str
    answer: str
    retrieval_sources: list[str]
    duration_s: float

    @property
    def route_ok(self) -> bool:
        return self.actual_route == self.case.route

    @property
    def retrieval_ok(self) -> bool | None:
        if self.case.route != "CAN_ANSWER" or not self.case.source:
            return None
        return self.case.source in self.retrieval_sources

    @property
    def answer_ok(self) -> bool:
        if not self.case.must_contain:
            return True
        lowered = self.answer.lower()
        return all(kw.lower() in lowered for kw in self.case.must_contain)


def load_cases(path: Path) -> list[Case]:
    cases: list[Case] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        cases.append(Case(**data))
    return cases


def run_case(case: Case) -> Result:
    start = time.perf_counter()
    actual_route = agent._classify(case.question)

    retrieval_sources: list[str] = []
    if actual_route == "CAN_ANSWER":
        chunks = hybrid.search(case.question, k=3)
        retrieval_sources = [c.source.name for c in chunks]

    reply = agent.answer(case.question)
    duration = time.perf_counter() - start

    return Result(
        case=case,
        actual_route=actual_route,
        answer=reply,
        retrieval_sources=retrieval_sources,
        duration_s=duration,
    )


def print_report(results: list[Result]) -> None:
    total = len(results)

    route_hits = sum(1 for r in results if r.route_ok)
    retrieval_total = sum(1 for r in results if r.retrieval_ok is not None)
    retrieval_hits = sum(1 for r in results if r.retrieval_ok is True)
    answer_hits = sum(1 for r in results if r.answer_ok)

    print()
    print("=" * 60)
    print("HRDesk Eval Results")
    print("=" * 60)
    print(f"Provider: {settings.llm_provider}")
    print(f"Total cases: {total}")
    print()
    print(f"Routing accuracy:   {route_hits}/{total}  ({_pct(route_hits, total)}%)")
    if retrieval_total:
        print(
            f"Retrieval hit@3:    {retrieval_hits}/{retrieval_total}  "
            f"({_pct(retrieval_hits, retrieval_total)}%)"
        )
    print(f"Answer correctness: {answer_hits}/{total}  ({_pct(answer_hits, total)}%)")
    print()

    failures = [r for r in results if not (r.route_ok and r.answer_ok)]
    if failures:
        print(f"Failures ({len(failures)}):")
        print("-" * 60)
        for r in failures:
            print(f"  [{r.case.id}] {r.case.question}")
            if not r.route_ok:
                print(f"    route: expected {r.case.route}, got {r.actual_route}")
            if r.retrieval_ok is False:
                print(
                    f"    retrieval: expected {r.case.source}, "
                    f"got {r.retrieval_sources}"
                )
            if not r.answer_ok:
                missing = [kw for kw in r.case.must_contain if kw.lower() not in r.answer.lower()]
                print(f"    answer missing: {missing}")
                print(f"    got: {r.answer[:120]!r}")
            print()
    else:
        print("All cases passed.")
    print("=" * 60)


def save_results(results: list[Result]) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = RESULTS_DIR / f"run_{settings.llm_provider}_{stamp}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(
                json.dumps(
                    {
                        "id": r.case.id,
                        "question": r.case.question,
                        "expected_route": r.case.route,
                        "actual_route": r.actual_route,
                        "route_ok": r.route_ok,
                        "retrieval_ok": r.retrieval_ok,
                        "retrieval_sources": r.retrieval_sources,
                        "answer_ok": r.answer_ok,
                        "answer": r.answer,
                        "duration_s": round(r.duration_s, 2),
                    }
                )
                + "\n"
            )
    return out


def _pct(num: int, denom: int) -> int:
    return round(100 * num / denom) if denom else 0


def main() -> None:
    chunks = ingest_directory(settings.data_dir)
    index_chunks(chunks)
    hybrid.build_index(chunks)

    cases = load_cases(GOLDEN_PATH)
    print(f"Running {len(cases)} eval cases against provider={settings.llm_provider}...")

    results: list[Result] = []
    for i, case in enumerate(cases, 1):
        print(f"  [{i}/{len(cases)}] {case.id}", flush=True)
        results.append(run_case(case))

    print_report(results)
    out = save_results(results)
    print(f"Detailed results saved to: {out.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
