from __future__ import annotations

import asyncio
from dataclasses import replace
from uuid import uuid4

from app.application.ports import GenerationEngine
from app.domain.generation import (
    BatchState,
    GenerationCommand,
    OfflineBatchJob,
    utc_now,
)


class OfflineBatchServing:
    """Durable-looking job API backed by an in-memory queue for this lesson.

    The client submits all prompts together and does not hold the POST request open.
    A single worker later executes one wide model call for the complete job.
    """

    def __init__(self, engine: GenerationEngine) -> None:
        self._engine = engine
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._jobs: dict[str, OfflineBatchJob] = {}
        self._done: dict[str, asyncio.Event] = {}

    def start(self) -> asyncio.Task[None]:
        return asyncio.create_task(self.run(), name="offline-batch-worker")

    async def stop(self) -> None:
        await self._queue.put(None)

    async def submit(self, commands: list[GenerationCommand]) -> OfflineBatchJob:
        job = OfflineBatchJob(job_id=str(uuid4()), commands=commands)
        self._jobs[job.job_id] = job
        self._done[job.job_id] = asyncio.Event()
        await self._queue.put(job.job_id)
        return self.snapshot(job.job_id)

    def get(self, job_id: str) -> OfflineBatchJob | None:
        if job_id not in self._jobs:
            return None
        return self.snapshot(job_id)

    async def wait(self, job_id: str) -> OfflineBatchJob:
        await self._done[job_id].wait()
        return self.snapshot(job_id)

    def snapshot(self, job_id: str) -> OfflineBatchJob:
        job = self._jobs[job_id]
        return replace(
            job,
            commands=list(job.commands),
            results=list(job.results) if job.results is not None else None,
        )

    async def run(self) -> None:
        while True:
            job_id = await self._queue.get()
            if job_id is None:
                return
            job = self._jobs[job_id]
            job.state = BatchState.RUNNING
            job.started_at = utc_now()
            try:
                token_limit = max(command.max_new_tokens for command in job.commands)
                prompts = [command.prompt for command in job.commands]
                results, inference_ms = await asyncio.to_thread(
                    self._engine.generate_batch,
                    prompts,
                    token_limit,
                )
                job.results = results
                job.inference_ms = inference_ms
                job.state = BatchState.COMPLETED
            except Exception as exc:  # noqa: BLE001 - persist failure in job state
                job.error = str(exc)
                job.state = BatchState.FAILED
            finally:
                job.completed_at = utc_now()
                self._done[job_id].set()
