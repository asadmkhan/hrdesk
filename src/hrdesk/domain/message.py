from typing import Any, Literal

from pydantic import BaseModel

Role = Literal["system", "user", "assistant", "tool"]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False


class Message(BaseModel):
    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = []
    tool_results: list[ToolResult] = []
