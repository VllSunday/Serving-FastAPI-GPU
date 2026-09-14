def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["device"] in {"cpu", "cuda"}
    assert body["model"]
    assert len(body["strategies"]) == 4


def test_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "LLM Serving Lab" in response.text


def test_gpu(client):
    response = client.get("/gpu")
    assert response.status_code == 200
    body = response.json()
    assert "device" in body
    assert "allocated_bytes" in body
    assert "reserved_bytes" in body
