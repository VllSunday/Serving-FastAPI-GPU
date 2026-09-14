from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    device: str = "auto"
    system_prompt: str = (
        "You are a factual assistant demonstrating model inference serving. "
        "Answer directly in the same language as the user, using 1-3 concise "
        "sentences unless asked otherwise. Never repeat the user's prompt. "
        "For machine-learning topics, clearly distinguish inference from training."
    )
    max_batch_size: int = 8
    max_wait_ms: int = 20
    default_max_new_tokens: int = 64
    max_new_tokens_cap: int = 128


settings = Settings()
