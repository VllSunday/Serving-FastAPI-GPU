from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from app.application.ports import GenerationEngine
from app.domain.generation import GenerationCommand, GenerationResult


class RealtimeServing:
    """Обычный request/response без прикладной очереди.

    Этапы:
    1. Получить команду от HTTP-слоя.
    2. Передать синхронный inference в отдельный поток.
    3. Дождаться одного вызова модели.
    4. Вернуть готовый текст и замеры клиенту одним ответом.
    """

    def __init__(self, engine: GenerationEngine) -> None:
        self._engine = engine

    async def generate(self, command: GenerationCommand) -> GenerationResult:
        # Полная latency начинается до передачи работы модели.
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
            # Явной очереди здесь нет. Ожидание model lock входит в latency_ms.
            queue_ms=0.0,
        )
