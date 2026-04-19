from typing import Any

from hrdesk.tools.base import Tool, ToolSchema
from hrdesk.tools.vacation import VacationTool

_TOOLS: dict[str, Tool] = {
    VacationTool.schema.name: VacationTool(),
}


def all_schemas() -> list[ToolSchema]:
    return [tool.schema for tool in _TOOLS.values()]


def run(name: str, arguments: dict[str, Any]) -> str:
    if name not in _TOOLS:
        return f"Unknown tool: {name}"
    return _TOOLS[name].run(arguments)
