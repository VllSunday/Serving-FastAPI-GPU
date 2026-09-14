from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from uuid import uuid4

from app.application.ports import GenerationEngine
from app.domain.generation import GenerationCommand, GenerationResult


@dataclass
class DynamicJob:
    command: GenerationCommand
    future: asyncio.Future[GenerationResult]
    request_id: str = field(default_factory=lambda: str(uuid4()))
    enqueued_at: float = field(default_factory=time.perf_counter)


class ContinuousBatchServing:
    """Merge independent requests that share generation parameters.

    HTTP requests wait on their own Future. The worker collects compatible jobs
    for a short time window, invokes the model once, then routes each result back
    to the matching Future.
    """

    def __init__(
        self,
        engine: GenerationEngine,
        max_batch_size: int,
        max_wait_ms: int,
    ) -> None:
        self._engine = engine
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self._queue: asyncio.Queue[DynamicJob | None] = asyncio.Queue()
        self._deferred: deque[DynamicJob] = deque()
        self.last_batch_size = 0
        self.last_wait_ms = 0.0
        self.last_inference_ms = 0.0
        self.last_batch_id: str | None = None
        self.total_batches = 0
        self.total_requests = 0

    def start(self) -> asyncio.Task[None]:
        return asyncio.create_task(self.run(), name="continuous-batch-worker")

    async def stop(self) -> None:
        await self._queue.put(None)

    def stats(self) -> dict:
        return {
            "last_batch_id": self.last_batch_id,
            "last_batch_size": self.last_batch_size,
            "last_wait_ms": self.last_wait_ms,
            "last_inference_ms": self.last_inference_ms,
            "total_batches": self.total_batches,
            "total_requests": self.total_requests,
            "queue_size": self._queue.qsize() + len(self._deferred),
            "max_batch_size": self.max_batch_size,
            "max_wait_ms": self.max_wait_ms,
        }

    async def submit(self, command: GenerationCommand) -> GenerationResult:
        future = asyncio.get_running_loop().create_future()
        job = DynamicJob(command=command, future=future)
        await self._queue.put(job)
        return await future

    async def run(self) -> None:
        while True:
            first = await self._next_job()
            if first is None:
                return
            batch = await self._collect_compatible(first)
            await self._execute(batch)

    async def _next_job(self) -> DynamicJob | None:
        while self._deferred:
            job = self._deferred.popleft()
            if not job.future.cancelled():
                return job
        return await self._queue.get()

    async def _collect_compatible(self, first: DynamicJob) -> list[DynamicJob]:
        batch = [first]
        deadline = first.enqueued_at + self.max_wait_ms / 1000

        while len(batch) < self.max_batch_size:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=remaining)
            except TimeoutError:
                break
            if job is None:
                await self._queue.put(None)
                break
            if job.future.cancelled():
                continue
            if job.command.max_new_tokens != first.command.max_new_tokens:
                self._deferred.append(job)
                break
            batch.append(job)

        self.last_wait_ms = round((time.perf_counter() - first.enqueued_at) * 1000, 2)
        return batch

    async def _execute(self, batch: list[DynamicJob]) -> None:
        batch_id = str(uuid4())
        prompts = [job.command.prompt for job in batch]
        token_limit = batch[0].command.max_new_tokens
        execution_started = time.perf_counter()
        try:
            texts, inference_ms = await asyncio.to_thread(
                self._engine.generate_batch,
                prompts,
                token_limit,
            )
            if len(texts) != len(batch):
                raise RuntimeError("batch result count does not match request count")
            for job, text in zip(batch, texts, strict=True):
                if job.future.done():
                    continue
                latency_ms = (time.perf_counter() - job.enqueued_at) * 1000
                job.future.set_result(
                    GenerationResult(
                        request_id=job.request_id,
                        mode="dynamic",
                        text=text,
                        latency_ms=latency_ms,
                        queue_ms=max(
                            0.0,
                            (execution_started - job.enqueued_at) * 1000,
                        ),
                        inference_ms=inference_ms,
                        batch_id=batch_id,
                        batch_size=len(batch),
                    )
                )
            self.last_inference_ms = round(inference_ms, 2)
        except Exception as exc:  # noqa: BLE001 - every job must receive worker errors
            for job in batch:
                if not job.future.done():
                    job.future.set_exception(exc)
        finally:
            self.last_batch_id = batch_id
            self.last_batch_size = len(batch)
            self.total_batches += 1
            self.total_requests += len(batch)
            elapsed_ms = (time.perf_counter() - execution_started) * 1000
            print(
                f"[continuous-batch] id={batch_id[:8]} size={len(batch)} "
                f"wait_ms={self.last_wait_ms:.1f} worker_ms={elapsed_ms:.1f}",
                flush=True,
            )
