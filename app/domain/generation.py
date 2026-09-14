from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class GenerationCommand:
    prompt: str
    max_new_tokens: int


@dataclass(frozen=True)
class EngineOutput:
    text: str
    inference_ms: float


@dataclass(frozen=True)
class GenerationResult:
    request_id: str
    mode: str
    text: str
    latency_ms: float
    inference_ms: float
    queue_ms: float = 0.0
    batch_id: str | None = None
    batch_size: int = 1


class BatchState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class OfflineBatchJob:
    job_id: str
    commands: list[GenerationCommand]
    state: BatchState = BatchState.QUEUED
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    results: list[str] | None = None
    inference_ms: float | None = None
    error: str | None = None

    @property
    def prompt_count(self) -> int:
        return len(self.commands)
