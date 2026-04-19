from langchain_anthropic import ChatAnthropic

from hrdesk.config import settings
from hrdesk.domain.message import Message
from hrdesk.providers._lc_messages import from_langchain_message, to_langchain_message


class AnthropicProvider:
    def __init__(self) -> None:
        if settings.anthropic_api_key is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._llm = ChatAnthropic(
            model_name=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            timeout=30,
            stop=None,
        )

    def chat(self, messages: list[Message]) -> Message:
        lc_messages = [to_langchain_message(m) for m in messages]
        reply = self._llm.invoke(lc_messages)
        return from_langchain_message(reply)
