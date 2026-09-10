from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable


InferFn = Callable[[list[str], int], list[str]]


@dataclass
class BatchJob:
    prompt: str
    max_new_tokens: int
    future: asyncio.Future
    enqueued_at: float = field(default_factory=time.perf_counter)


class Batcher:
    """Dynamic batcher: independent HTTP requests share one GPU call.

    HTTP → asyncio.Queue → this worker → one batched generate() → per-request futures.
    """

    def __init__(
        self,
        infer_fn: InferFn,
        max_batch_size: int,
        max_wait_ms: int,
    ) -> None:
        self.infer_fn = infer_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.queue: asyncio.Queue[BatchJob] = asyncio.Queue()
        self._running = False
        self.last_batch_size = 0
        self.last_wait_ms = 0.0
        self.total_batches = 0
        self.total_requests = 0

    def stats(self) -> dict:
        return {
            "last_batch_size": self.last_batch_size,
            "last_wait_ms": self.last_wait_ms,
            "total_batches": self.total_batches,
            "total_requests": self.total_requests,
            "queue_size": self.queue.qsize(),
            "max_batch_size": self.max_batch_size,
            "max_wait_ms": self.max_wait_ms,
        }

    async def submit(self, prompt: str, max_new_tokens: int) -> str:
        loop = asyncio.get_running_loop()
        job = BatchJob(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            future=loop.create_future(),
        )
        await self.queue.put(job)
        return await job.future

    async def run(self) -> None:
        self._running = True
        while self._running:
            first = await self.queue.get()
            if first is None:  # type: ignore[comparison-overlap]
                break
            await self._process_batch(first)

    async def stop(self) -> None:
        self._running = False
        await self.queue.put(None)  # type: ignore[arg-type]

    async def _process_batch(self, first: BatchJob) -> None:
        # TODO(student):
        # collect requests into a batch
        # respect MAX_BATCH_SIZE
        # respect MAX_WAIT_MS
        # execute one GPU inference
        # return each result to the correct request
        batch = await self._collect_batch(first)
        await self._execute_and_return(batch)

    async def _collect_batch(self, first: BatchJob) -> list[BatchJob]:
        """Wait up to MAX_WAIT_MS or until MAX_BATCH_SIZE jobs are ready."""
        batch = [first]
        deadline = first.enqueued_at + (self.max_wait_ms / 1000.0)

        while len(batch) < self.max_batch_size:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                break
            try:
                job = await asyncio.wait_for(self.queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                break
            if job is None:  # type: ignore[comparison-overlap]
                await self.queue.put(None)  # type: ignore[arg-type]
                break
            batch.append(job)

        wait_ms = (time.perf_counter() - first.enqueued_at) * 1000
        print(f"[batcher] batch_size={len(batch)} wait_ms={wait_ms:.1f}", flush=True)
        self.last_batch_size = len(batch)
        self.last_wait_ms = round(wait_ms, 1)
        self.total_batches += 1
        self.total_requests += len(batch)
        return batch

    async def _execute_and_return(self, batch: list[BatchJob]) -> None:
        prompts = [job.prompt for job in batch]
        max_new_tokens = max(job.max_new_tokens for job in batch)

        try:
            texts = await asyncio.to_thread(self.infer_fn, prompts, max_new_tokens)
            if len(texts) != len(batch):
                raise RuntimeError("batch result count does not match request count")
            for job, text in zip(batch, texts, strict=True):
                if not job.future.done():
                    job.future.set_result(text)
        except Exception as exc:
            for job in batch:
                if not job.future.done():
                    job.future.set_exception(exc)
