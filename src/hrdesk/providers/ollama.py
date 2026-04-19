import httpx
from langchain_ollama import ChatOllama

from hrdesk.config import settings
from hrdesk.domain.message import Message
from hrdesk.providers._lc_messages import from_langchain_message, to_langchain_message


class OllamaProvider:
    def __init__(self) -> None:
        self._llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    @staticmethod
    def is_available() -> bool:
        try:
            r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=1.5)
            return r.status_code == 200
        except httpx.RequestError:
            return False

    def chat(self, messages: list[Message]) -> Message:
        lc_messages = [to_langchain_message(m) for m in messages]
        reply = self._llm.invoke(lc_messages)
        return from_langchain_message(reply)
