from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.metrics import gpu_snapshot
from app.model.inference import generate_batch
from app.model.loader import load_model
from app.schemas import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
)
from app.serving.batcher import Batcher
from app.serving.simple import run_simple
from app.serving.streaming import stream_generate


def _clamp_tokens(max_new_tokens: int) -> int:
    return max(1, min(max_new_tokens, settings.max_new_tokens_cap))


@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = load_model()
    app.state.bundle = bundle

    def infer_fn(prompts: list[str], max_new_tokens: int) -> list[str]:
        texts, _latency_ms = generate_batch(bundle, prompts, max_new_tokens)
        return texts

    batcher = Batcher(
        infer_fn=infer_fn,
        max_batch_size=settings.max_batch_size,
        max_wait_ms=settings.max_wait_ms,
    )
    app.state.batcher = batcher
    worker = asyncio.create_task(batcher.run())
    try:
        yield
    finally:
        await batcher.stop()
        worker.cancel()


app = FastAPI(title="GPU Serving Course", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    bundle = request.app.state.bundle
    return HealthResponse(
        status="ok",
        device=bundle.device,
        gpu=bundle.gpu_name,
        model=bundle.model_name,
    )


@app.get("/gpu")
def gpu(request: Request) -> dict:
    bundle = request.app.state.bundle
    return gpu_snapshot(bundle.device)


@app.get("/batcher/stats")
def batcher_stats(request: Request) -> dict:
    return request.app.state.batcher.stats()


@app.post("/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, request: Request) -> GenerateResponse:
    bundle = request.app.state.bundle
    text, latency_ms = run_simple(
        bundle,
        payload.prompt,
        _clamp_tokens(payload.max_new_tokens),
    )
    return GenerateResponse(text=text, latency_ms=round(latency_ms, 2))


@app.post("/generate/batch", response_model=BatchGenerateResponse)
def generate_batch_endpoint(
    payload: BatchGenerateRequest,
    request: Request,
) -> BatchGenerateResponse:
    bundle = request.app.state.bundle
    texts, latency_ms = generate_batch(
        bundle,
        payload.prompts,
        _clamp_tokens(payload.max_new_tokens),
    )
    return BatchGenerateResponse(
        results=texts,
        batch_size=len(payload.prompts),
        latency_ms=round(latency_ms, 2),
    )


@app.post("/generate/dynamic", response_model=GenerateResponse)
async def generate_dynamic(payload: GenerateRequest, request: Request) -> GenerateResponse:
    batcher: Batcher = request.app.state.batcher
    started = time.perf_counter()
    text = await batcher.submit(payload.prompt, _clamp_tokens(payload.max_new_tokens))
    latency_ms = (time.perf_counter() - started) * 1000
    return GenerateResponse(text=text, latency_ms=round(latency_ms, 2))


@app.post("/generate/stream")
async def generate_stream(payload: GenerateRequest, request: Request) -> StreamingResponse:
    bundle = request.app.state.bundle
    return StreamingResponse(
        stream_generate(bundle, payload.prompt, _clamp_tokens(payload.max_new_tokens)),
        media_type="text/plain",
    )
