from hrdesk.config import LLMProvider, settings
from hrdesk.providers.anthropic import AnthropicProvider
from hrdesk.providers.base import ChatProvider
from hrdesk.providers.ollama import OllamaProvider


def get_provider() -> ChatProvider:
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        return AnthropicProvider()
    if settings.llm_provider == LLMProvider.OLLAMA:
        return OllamaProvider()
    raise ValueError(f"Unsupported provider: {settings.llm_provider}")
