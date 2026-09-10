from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _strip_env_quotes(value: str) -> str:
    """systemd EnvironmentFile keeps literal quotes; AvalAI rejects quoted model names."""
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
        cleaned = cleaned[1:-1].strip()
    return cleaned


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    avalai_base_url: str = "https://api.avalai.ir/v1"
    avalai_api_key: str = ""
    default_model: str = "gpt-5.6-luna"
    request_timeout_seconds: float = 120.0
    max_history_turns: int = 20
    max_output_tokens: int = 500

    @field_validator("avalai_base_url", "avalai_api_key", "default_model", mode="before")
    @classmethod
    def normalize_env_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return _strip_env_quotes(value)
        return value


settings = Settings()
