from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm_provider: LLMProvider = LLMProvider.ANTHROPIC

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-4-6"

    ollama_model: str = "llama3.2:3b"
    ollama_base_url: str = "http://localhost:11434"

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    data_dir: Path = PROJECT_ROOT / "data"
    chroma_dir: Path = PROJECT_ROOT / ".chroma"

    hr_api_base_url: str = "http://localhost:8001"

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["console", "json"] = "console"


settings = Settings()
