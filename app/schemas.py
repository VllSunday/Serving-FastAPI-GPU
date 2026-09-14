from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Prompt = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class GenerateRequest(BaseModel):
    prompt: Prompt
    max_new_tokens: int = Field(default=64, ge=1, le=256)


class GenerateResponse(BaseModel):
    request_id: str
    mode: Literal["realtime", "dynamic"]
    text: str
    latency_ms: float
    queue_ms: float
    inference_ms: float
    batch_id: str | None = None
    batch_size: int = 1


class BatchGenerateRequest(BaseModel):
    prompts: list[Prompt] = Field(min_length=1, max_length=64)
    max_new_tokens: int = Field(default=64, ge=1, le=256)


class BatchGenerateResponse(BaseModel):
    results: list[str]
    batch_size: int
    latency_ms: float


class BatchAcceptedResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    prompt_count: int
    status_url: str


class BatchJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    prompt_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    inference_ms: float | None
    results: list[str] | None
    error: str | None


class HealthResponse(BaseModel):
    status: str
    device: str
    gpu: str | None
    model: str
    strategies: list[str]
