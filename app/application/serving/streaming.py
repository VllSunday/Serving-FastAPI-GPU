from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Iterator
from uuid import uuid4

from app.application.ports import GenerationEngine
from app.domain.generation import GenerationCommand


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _next_chunk(iterator: Iterator[str]) -> str | None:
    try:
        return next(iterator)
    except StopIteration:
        return None


class StreamingServing:
    """Expose partial decoded text while synchronous generation is still running."""

    def __init__(self, engine: GenerationEngine) -> None:
        self._engine = engine

    async def events(self, command: GenerationCommand) -> AsyncIterator[str]:
        request_id = str(uuid4())
        started = time.perf_counter()
        yield _sse("start", {"request_id": request_id, "mode": "stream"})

        iterator = self._engine.stream(command.prompt, command.max_new_tokens)
        text = ""
        chunk_index = 0
        while True:
            piece = await asyncio.to_thread(_next_chunk, iterator)
            if piece is None:
                break
            if not piece:
                continue
            text += piece
            chunk_index += 1
            yield _sse(
                "token",
                {
                    "request_id": request_id,
                    "index": chunk_index,
                    "delta": piece,
                    "text": text,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )

        yield _sse(
            "done",
            {
                "request_id": request_id,
                "text": text,
                "chunks": chunk_index,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
