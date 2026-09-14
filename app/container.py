from __future__ import annotations

from dataclasses import dataclass

from app.application.serving.continuous_batch import ContinuousBatchServing
from app.application.serving.offline_batch import OfflineBatchServing
from app.application.serving.realtime import RealtimeServing
from app.application.serving.streaming import StreamingServing
from app.infrastructure.transformers_engine import TransformersEngine


@dataclass(frozen=True)
class ServiceContainer:
    """Объекты, которые composition root собирает в app.main."""

    engine: TransformersEngine
    realtime: RealtimeServing
    offline_batch: OfflineBatchServing
    continuous_batch: ContinuousBatchServing
    streaming: StreamingServing
