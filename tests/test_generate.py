def test_generate(client):
    response = client.post(
        "/generate",
        json={"prompt": "Hello", "max_new_tokens": 4},
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["text"], str)
    assert body["text"]
    assert body["latency_ms"] >= 0


def test_generate_batch(client):
    response = client.post(
        "/generate/batch",
        json={
            "prompts": ["FastAPI", "CUDA", "batching"],
            "max_new_tokens": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["batch_size"] == 3
    assert len(body["results"]) == 3
    assert body["latency_ms"] >= 0


def test_generate_stream(client):
    with client.stream(
        "POST",
        "/generate/stream",
        json={"prompt": "Hello", "max_new_tokens": 4},
    ) as response:
        assert response.status_code == 200
        chunks = "".join(response.iter_text())
    assert "event: start" in chunks
    assert "event: token" in chunks
    assert "event: done" in chunks


def test_assignment_spelling_alias(client):
    response = client.post(
        "/generate/dinamic",
        json={"prompt": "Hello", "max_new_tokens": 4},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "dynamic"
