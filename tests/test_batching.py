import asyncio

from app.serving.batcher import Batcher


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
    seen_sizes: list[int] = []

    def infer_fn(prompts: list[str], max_new_tokens: int) -> list[str]:
        seen_sizes.append(len(prompts))
        return [f"out:{prompt}" for prompt in prompts]

    async def scenario() -> None:
        batcher = Batcher(infer_fn=infer_fn, max_batch_size=4, max_wait_ms=80)
        worker = asyncio.create_task(batcher.run())
        texts = await asyncio.gather(
            batcher.submit("a", 8),
            batcher.submit("b", 8),
            batcher.submit("c", 8),
            batcher.submit("d", 8),
        )
        await batcher.stop()
        worker.cancel()
        assert texts == ["out:a", "out:b", "out:c", "out:d"]
        assert seen_sizes[0] == 4
        assert batcher.last_batch_size == 4

    asyncio.run(scenario())
