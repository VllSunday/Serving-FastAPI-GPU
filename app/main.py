from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.application.serving.continuous_batch import ContinuousBatchServing
from app.application.serving.offline_batch import OfflineBatchServing
from app.application.serving.realtime import RealtimeServing
from app.application.serving.streaming import StreamingServing
from app.config import settings
from app.container import ServiceContainer
from app.infrastructure.transformers_engine import TransformersEngine
from app.model.loader import load_model
from app.presentation.api import router

STATIC_DIR = Path(__file__).parent / "presentation" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = TransformersEngine(load_model())
    offline_batch = OfflineBatchServing(engine)
    continuous_batch = ContinuousBatchServing(
        engine,
        max_batch_size=settings.max_batch_size,
        max_wait_ms=settings.max_wait_ms,
    )
    app.state.services = ServiceContainer(
        engine=engine,
        realtime=RealtimeServing(engine),
        offline_batch=offline_batch,
        continuous_batch=continuous_batch,
        streaming=StreamingServing(engine),
    )
    workers = [offline_batch.start(), continuous_batch.start()]
    try:
        yield
    finally:
        await offline_batch.stop()
        await continuous_batch.stop()
        await asyncio.gather(*workers, return_exceptions=True)


app = FastAPI(
    title="LLM Serving Lab",
    description="Четыре наглядные стратегии сервинга с общей моделью.",
    lifespan=lifespan,
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
