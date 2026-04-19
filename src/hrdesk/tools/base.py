from typing import Any, Protocol

from pydantic import BaseModel


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class Tool(Protocol):
    schema: ToolSchema

    def run(self, arguments: dict[str, Any], auth_user_id: str) -> str: ...
