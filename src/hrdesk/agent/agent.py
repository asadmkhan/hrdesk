import json
import re

from hrdesk.agent.prompts import (
    ANSWER_SYSTEM_PROMPT,
    CLASSIFIER_SYSTEM_PROMPT,
    NO_MATCH_REPLY,
    TOOL_ANSWER_SYSTEM_PROMPT,
    TOOL_SELECTION_TEMPLATE,
)
from hrdesk.config import LLMProvider
from hrdesk.domain.document import Chunk
from hrdesk.domain.message import Message
from hrdesk.observability.logging import get_logger
from hrdesk.providers.factory import get_provider
from hrdesk.retrieval import hybrid
from hrdesk.tools import registry
from hrdesk.tools.base import ToolSchema

log = get_logger(__name__)

CURRENT_EMPLOYEE_ID = "E001"

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)

_OTHER_USER_REPLY = (
    "I can only look up your own HR data. For questions about other employees, "
    "please contact HR directly."
)

_TOOL_SELECTION_FAILED = "I tried to look that up but couldn't determine which tool to use."


def answer(question: str, provider_override: LLMProvider | None = None) -> str:
    route = _classify(question, provider_override)
    log.info("agent_routed", question=question, route=route)

    if route == "CAN_ANSWER":
        return _answer_from_docs(question, provider_override)
    if route == "CALL_EXTERNAL_TOOL":
        return _answer_via_tool(question, provider_override)
    return NO_MATCH_REPLY


def _classify(question: str, provider_override: LLMProvider | None = None) -> str:
    provider = get_provider(provider_override)
    reply = provider.chat(
        [
            Message(role="system", content=CLASSIFIER_SYSTEM_PROMPT),
            Message(role="user", content=question),
        ]
    )
    label = reply.content.strip().upper()
    if label not in ("CAN_ANSWER", "CALL_EXTERNAL_TOOL", "NO_MATCH"):
        log.warning("classifier_bad_label", raw=reply.content)
        return "NO_MATCH"
    return label


def _answer_from_docs(question: str, provider_override: LLMProvider | None = None) -> str:
    chunks = hybrid.search(question, k=3)
    if not chunks:
        return "I could not find any relevant information in the HR documents."

    provider = get_provider(provider_override)
    reply = provider.chat(
        [
            Message(role="system", content=ANSWER_SYSTEM_PROMPT),
            Message(role="user", content=_build_rag_user_prompt(question, chunks)),
        ]
    )
    return reply.content


def _answer_via_tool(question: str, provider_override: LLMProvider | None = None) -> str:
    if _asks_about_another_person(question):
        log.info("tool_request_about_other_person", question=question)
        return _OTHER_USER_REPLY

    provider = get_provider(provider_override)
    selection = provider.chat(
        [
            Message(role="system", content=_build_tool_selection_prompt(registry.all_schemas())),
            Message(role="user", content=f"User: {question}\nOutput:"),
        ]
    )

    tool_name, arguments = _parse_tool_selection(selection.content)
    if tool_name is None:
        return _TOOL_SELECTION_FAILED

    tool_result = registry.run(tool_name, arguments, CURRENT_EMPLOYEE_ID)
    log.info("tool_executed", tool=tool_name)

    reply = provider.chat(
        [
            Message(role="system", content=TOOL_ANSWER_SYSTEM_PROMPT),
            Message(role="user", content=_build_tool_answer_prompt(question, tool_result)),
        ]
    )
    return reply.content


def _build_rag_user_prompt(question: str, chunks: list[Chunk]) -> str:
    context = "\n\n".join(f"[source: {c.source.name}]\n{c.text}" for c in chunks)
    return f"Context:\n{context}\n\nQuestion: {question}"


def _build_tool_selection_prompt(schemas: list[ToolSchema]) -> str:
    tool_list = "\n".join(f"- {s.name}: {s.description}" for s in schemas)
    return TOOL_SELECTION_TEMPLATE.format(tool_list=tool_list)


def _build_tool_answer_prompt(question: str, tool_result: str) -> str:
    return f"Question: {question}\n\nTool result: {tool_result}"


def _parse_tool_selection(raw: str) -> tuple[str | None, dict]:
    match = _JSON_OBJECT.search(raw)
    if match is None:
        log.warning("tool_selection_no_json", raw=raw)
        return None, {}

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        log.warning("tool_selection_bad_json", raw=raw)
        return None, {}

    return parsed.get("tool") or None, parsed.get("arguments", {}) or {}


def _asks_about_another_person(question: str) -> bool:
    q = question.lower()
    third_party_markers = [
        " for ",
        " about ",
        " does ",
        "employee ",
        "'s ",
        "he ",
        "she ",
        "they ",
        "his ",
        "her ",
        "their ",
    ]
    self_markers = ["my ", "me", " i ", " i'", "mine"]
    has_third_party = any(m in q for m in third_party_markers)
    has_self = any(m in q for m in self_markers) or q.strip().startswith(("i ", "i'"))
    return has_third_party and not has_self
