from hrdesk.config import LLMProvider, settings
from hrdesk.providers.anthropic import AnthropicProvider
from hrdesk.providers.base import ChatProvider
from hrdesk.providers.ollama import OllamaProvider

_REGISTRY = {
    LLMProvider.ANTHROPIC: AnthropicProvider,
    LLMProvider.OLLAMA: OllamaProvider,
}

_cache: dict[LLMProvider, ChatProvider] = {}


def get_provider(override: LLMProvider | None = None) -> ChatProvider:
    choice = override or settings.llm_provider
    cls = _REGISTRY.get(choice)
    if cls is None:
        raise ValueError(f"Unsupported provider: {choice}")
    if choice not in _cache:
        _cache[choice] = cls()
    return _cache[choice]


def available_providers() -> list[LLMProvider]:
    return [name for name, cls in _REGISTRY.items() if cls.is_available()]
