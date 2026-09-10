import os

os.environ.setdefault("MODEL_NAME", "sshleifer/tiny-gpt2")
os.environ.setdefault("DEVICE", "cpu")
os.environ.setdefault("MAX_BATCH_SIZE", "4")
os.environ.setdefault("MAX_WAIT_MS", "80")
os.environ.setdefault("MAX_NEW_TOKENS_CAP", "16")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
