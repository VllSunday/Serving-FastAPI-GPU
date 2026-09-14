from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from app.application.ports import GenerationEngine
from app.domain.generation import GenerationCommand, GenerationResult


class RealtimeServing:
    """One request maps directly to one model invocation."""

    def __init__(self, engine: GenerationEngine) -> None:
        self._engine = engine

    async def generate(self, command: GenerationCommand) -> GenerationResult:
        started = time.perf_counter()
        output = await asyncio.to_thread(
            self._engine.generate,
            command.prompt,
            command.max_new_tokens,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        return GenerationResult(
            request_id=str(uuid4()),
            mode="realtime",
            text=output.text,
            latency_ms=latency_ms,
            inference_ms=output.inference_ms,
            queue_ms=0.0,
        )
