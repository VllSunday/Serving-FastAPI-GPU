import asyncio
import time

from app.application.serving.continuous_batch import ContinuousBatchServing
from app.domain.generation import EngineOutput, GenerationCommand


class FakeEngine:
    def __init__(self) -> None:
        self.seen_sizes: list[int] = []

    def generate(self, prompt: str, max_new_tokens: int) -> EngineOutput:
        return EngineOutput(text=f"out:{prompt}", inference_ms=1.0)

    def generate_batch(
        self,
        prompts: list[str],
        max_new_tokens: int,
    ) -> tuple[list[str], float]:
        self.seen_sizes.append(len(prompts))
        return [f"out:{prompt}" for prompt in prompts], 1.0

    def stream(self, prompt: str, max_new_tokens: int):
        yield "out"


def test_dynamic_generate(client):
    response = client.post(
        "/generate/dynamic",
        json={"prompt": "Explain serving", "max_new_tokens": 4},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"]
    assert body["latency_ms"] >= 0


def test_batcher_stats_endpoint(client):
    response = client.get("/batcher/stats")
    assert response.status_code == 200
    body = response.json()
    assert "max_batch_size" in body
    assert "max_wait_ms" in body


def test_batcher_merges_independent_requests():
    async def scenario() -> None:
        engine = FakeEngine()
        batcher = ContinuousBatchServing(engine, max_batch_size=4, max_wait_ms=80)
        worker = batcher.start()
        results = await asyncio.gather(
            batcher.submit(GenerationCommand("a", 8)),
            batcher.submit(GenerationCommand("b", 8)),
            batcher.submit(GenerationCommand("c", 8)),
            batcher.submit(GenerationCommand("d", 8)),
        )
        await batcher.stop()
        await worker
        assert [result.text for result in results] == ["out:a", "out:b", "out:c", "out:d"]
        assert engine.seen_sizes == [4]
        assert batcher.last_batch_size == 4
        assert len({result.batch_id for result in results}) == 1

    asyncio.run(scenario())


def test_batcher_does_not_mix_incompatible_token_limits():
    async def scenario() -> None:
        engine = FakeEngine()
        batcher = ContinuousBatchServing(engine, max_batch_size=4, max_wait_ms=5)
        worker = batcher.start()
        first = asyncio.create_task(batcher.submit(GenerationCommand("short", 4)))
        second = asyncio.create_task(batcher.submit(GenerationCommand("long", 8)))
        results = await asyncio.gather(first, second)
        await batcher.stop()
        await worker
        assert engine.seen_sizes == [1, 1]
        assert results[0].batch_id != results[1].batch_id

    asyncio.run(scenario())


def test_offline_batch_job(client):
    accepted = client.post(
        "/batch",
        json={"prompts": ["FastAPI", "CUDA", "batching"], "max_new_tokens": 4},
    )
    assert accepted.status_code == 202
    body = accepted.json()
    assert body["prompt_count"] == 3

    deadline = time.monotonic() + 10
    job = None
    while time.monotonic() < deadline:
        response = client.get(body["status_url"])
        assert response.status_code == 200
        job = response.json()
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)

    assert job is not None
    assert job["status"] == "completed"
    assert len(job["results"]) == 3
    assert job["inference_ms"] >= 0
