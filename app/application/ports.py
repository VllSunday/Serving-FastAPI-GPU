from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from app.domain.generation import EngineOutput


class GenerationEngine(Protocol):
    """Контракт, который инфраструктурный адаптер реализует для use cases."""

    def generate(self, prompt: str, max_new_tokens: int) -> EngineOutput: ...

    def generate_batch(
        self,
        prompts: list[str],
        max_new_tokens: int,
    ) -> tuple[list[str], float]: ...

    def stream(self, prompt: str, max_new_tokens: int) -> Iterator[str]: ...
