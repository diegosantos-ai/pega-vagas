import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações globais do projeto validadas pelo Pydantic.
    Lê do arquivo .env automaticamente.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- LLM ---
    GOOGLE_API_KEY: str | None = None
    LLM_MODEL: str = "gemini-2.0-flash"

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    # --- Proxy ---
    PROXY_URL: str | None = None
    
    # --- Paths ---
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # --- Pipeline ---
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    def has_telegram_config(self) -> bool:
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)

    def has_llm_config(self) -> bool:
        return bool(self.GOOGLE_API_KEY)


# Instância global (singleton)
settings = Settings()
