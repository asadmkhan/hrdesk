from hrdesk.config import LLMProvider, settings
from hrdesk.providers.anthropic import AnthropicProvider
from hrdesk.providers.base import ChatProvider
from hrdesk.providers.ollama import OllamaProvider

_REGISTRY = {
    LLMProvider.ANTHROPIC: AnthropicProvider,
    LLMProvider.OLLAMA: OllamaProvider,
}


def get_provider(override: LLMProvider | None = None) -> ChatProvider:
    choice = override or settings.llm_provider
    cls = _REGISTRY.get(choice)
    if cls is None:
        raise ValueError(f"Unsupported provider: {choice}")
    return cls()


def available_providers() -> list[LLMProvider]:
    return [name for name, cls in _REGISTRY.items() if cls.is_available()]
