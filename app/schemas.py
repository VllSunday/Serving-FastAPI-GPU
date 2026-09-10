from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_new_tokens: int = Field(default=64, ge=1, le=256)


class GenerateResponse(BaseModel):
    text: str
    latency_ms: float


class BatchGenerateRequest(BaseModel):
    prompts: list[str] = Field(min_length=1)
    max_new_tokens: int = Field(default=64, ge=1, le=256)


class BatchGenerateResponse(BaseModel):
    results: list[str]
    batch_size: int
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
    device: str
    gpu: str | None
    model: str
