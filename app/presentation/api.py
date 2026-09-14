from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.config import settings
from app.container import ServiceContainer
from app.domain.generation import (
    BatchState,
    GenerationCommand,
    GenerationResult,
    OfflineBatchJob,
)
from app.metrics import gpu_snapshot
from app.schemas import (
    BatchAcceptedResponse,
    BatchGenerateRequest,
    BatchGenerateResponse,
    BatchJobResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
)

router = APIRouter()


def services(request: Request) -> ServiceContainer:
    return request.app.state.services


def clamp_tokens(value: int) -> int:
    return max(1, min(value, settings.max_new_tokens_cap))


def command(payload: GenerateRequest) -> GenerationCommand:
    return GenerationCommand(payload.prompt, clamp_tokens(payload.max_new_tokens))


def generation_response(result: GenerationResult) -> GenerateResponse:
    return GenerateResponse(
        request_id=result.request_id,
        mode=result.mode,
        text=result.text,
        latency_ms=round(result.latency_ms, 2),
        queue_ms=round(result.queue_ms, 2),
        inference_ms=round(result.inference_ms, 2),
        batch_id=result.batch_id,
        batch_size=result.batch_size,
    )


def batch_response(job: OfflineBatchJob) -> BatchJobResponse:
    return BatchJobResponse(
        job_id=job.job_id,
        status=job.state,
        prompt_count=job.prompt_count,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        inference_ms=round(job.inference_ms, 2) if job.inference_ms is not None else None,
        results=job.results,
        error=job.error,
    )


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    bundle = services(request).engine.bundle
    return HealthResponse(
        status="ok",
        device=bundle.device,
        gpu=bundle.gpu_name,
        model=bundle.model_name,
        strategies=["realtime", "offline_batch", "continuous_batch", "streaming"],
    )


@router.get("/gpu", tags=["system"])
def gpu(request: Request) -> dict:
    return gpu_snapshot(services(request).engine.bundle.device)


@router.get("/batcher/stats", tags=["continuous batching"])
def batcher_stats(request: Request) -> dict:
    return services(request).continuous_batch.stats()


@router.post("/generate", response_model=GenerateResponse, tags=["1 · realtime"])
async def generate(payload: GenerateRequest, request: Request) -> GenerateResponse:
    result = await services(request).realtime.generate(command(payload))
    return generation_response(result)


@router.post(
    "/batch",
    response_model=BatchAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["2 · offline batch"],
)
async def create_batch(
    payload: BatchGenerateRequest,
    request: Request,
) -> BatchAcceptedResponse:
    token_limit = clamp_tokens(payload.max_new_tokens)
    commands = [GenerationCommand(prompt, token_limit) for prompt in payload.prompts]
    job = await services(request).offline_batch.submit(commands)
    return BatchAcceptedResponse(
        job_id=job.job_id,
        status=job.state,
        prompt_count=job.prompt_count,
        status_url=f"/batch/{job.job_id}",
    )


@router.get("/batch/{job_id}", response_model=BatchJobResponse, tags=["2 · offline batch"])
def get_batch(job_id: str, request: Request) -> BatchJobResponse:
    job = services(request).offline_batch.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="batch job not found")
    return batch_response(job)


@router.post(
    "/generate/batch",
    response_model=BatchGenerateResponse,
    include_in_schema=False,
)
async def legacy_generate_batch(
    payload: BatchGenerateRequest,
    request: Request,
) -> BatchGenerateResponse:
    """Compatibility route from the teacher's starter repository."""
    token_limit = clamp_tokens(payload.max_new_tokens)
    commands = [GenerationCommand(prompt, token_limit) for prompt in payload.prompts]
    submitted = await services(request).offline_batch.submit(commands)
    completed = await services(request).offline_batch.wait(submitted.job_id)
    if completed.state is BatchState.FAILED:
        raise HTTPException(status_code=500, detail=completed.error)
    return BatchGenerateResponse(
        results=completed.results or [],
        batch_size=completed.prompt_count,
        latency_ms=round(completed.inference_ms or 0.0, 2),
    )


async def dynamic_response(payload: GenerateRequest, request: Request) -> GenerateResponse:
    result = await services(request).continuous_batch.submit(command(payload))
    return generation_response(result)


@router.post(
    "/generate/dynamic",
    response_model=GenerateResponse,
    tags=["3 · continuous batch"],
)
async def generate_dynamic(payload: GenerateRequest, request: Request) -> GenerateResponse:
    return await dynamic_response(payload, request)


@router.post(
    "/generate/dinamic",
    response_model=GenerateResponse,
    include_in_schema=False,
)
async def generate_dinamic_alias(
    payload: GenerateRequest,
    request: Request,
) -> GenerateResponse:
    """Alias for the spelling used in the assignment text."""
    return await dynamic_response(payload, request)


@router.post("/generate/stream", tags=["4 · streaming"])
async def generate_stream(payload: GenerateRequest, request: Request) -> StreamingResponse:
    return StreamingResponse(
        services(request).streaming.events(command(payload)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
