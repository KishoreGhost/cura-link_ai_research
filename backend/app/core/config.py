from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Curalink API'
    environment: Literal['development', 'staging', 'production'] = 'development'
    api_v1_prefix: str = '/api/v1'
    allowed_origins: str = 'http://localhost:5173'
    mongodb_url: str = 'mongodb://localhost:27017/curalink'
    ollama_base_url: str = 'http://localhost:11434'
    ollama_chat_model: str = 'gemma4:e4b'
    default_candidate_target: int = 150


@lru_cache
def get_settings() -> Settings:
    return Settings()
