from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from hrdesk.domain.message import Message


def to_langchain_message(msg: Message) -> BaseMessage:
    if msg.role == "system":
        return SystemMessage(content=msg.content)
    if msg.role == "user":
        return HumanMessage(content=msg.content)
    if msg.role == "assistant":
        return AIMessage(content=msg.content)
    if msg.role == "tool":
        result = msg.tool_results[0] if msg.tool_results else None
        return ToolMessage(
            content=result.content if result else "",
            tool_call_id=result.tool_call_id if result else "",
        )
    raise ValueError(f"Unknown role: {msg.role}")


def from_langchain_message(msg: BaseMessage) -> Message:
    return Message(role="assistant", content=str(msg.content))
