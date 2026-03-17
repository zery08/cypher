from pathlib import Path
from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Graph Chat API"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    neo4j_uri: str = ""
    neo4j_username: str = ""
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    schema_cache_ttl_seconds: int = 60

    llm_base_url: str = Field(
        default="https://api.z.ai/api/paas/v4",
        validation_alias=AliasChoices(
            "LLM_BASE_URL",
            "ZAI_BASE_URL",
            "GEMINI_BASE_URL",
            "OPENAI_BASE_URL",
        ),
    )
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LLM_API_KEY",
            "ZAI_API_KEY",
            "GEMINI_API_KEY",
            "OPENAI_API_KEY",
        ),
    )
    llm_model: str = Field(
        default="glm-4.7",
        validation_alias=AliasChoices(
            "LLM_MODEL",
            "ZAI_MODEL",
            "GEMINI_MODEL",
            "OPENAI_MODEL",
        ),
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def neo4j_configured(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_username and self.neo4j_password)

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
