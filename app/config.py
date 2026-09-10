from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    model_name: str = "distilgpt2"
    device: str = "auto"
    max_batch_size: int = 8
    max_wait_ms: int = 20
    default_max_new_tokens: int = 64
    max_new_tokens_cap: int = 128


settings = Settings()
