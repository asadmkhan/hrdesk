from typing import Protocol

from hrdesk.domain.message import Message


class ChatProvider(Protocol):
    def chat(self, messages: list[Message]) -> Message: ...
