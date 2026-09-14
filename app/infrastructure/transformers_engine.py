from __future__ import annotations

from collections.abc import Iterator
from threading import Lock, Thread

import torch
from transformers import TextIteratorStreamer

from app.domain.generation import EngineOutput
from app.model.inference import generate_batch, generate_one
from app.model.loader import ModelBundle


class TransformersEngine:
    """Hugging Face implementation of the application engine port.

    One process owns one model. The lock prevents unrelated endpoint strategies
    from launching competing generate calls on the same GPU at the same time.
    """

    def __init__(self, bundle: ModelBundle) -> None:
        self.bundle = bundle
        self._model_lock = Lock()

    def generate(self, prompt: str, max_new_tokens: int) -> EngineOutput:
        with self._model_lock:
            text, inference_ms = generate_one(self.bundle, prompt, max_new_tokens)
        return EngineOutput(text=text, inference_ms=inference_ms)

    def generate_batch(
        self,
        prompts: list[str],
        max_new_tokens: int,
    ) -> tuple[list[str], float]:
        with self._model_lock:
            return generate_batch(self.bundle, prompts, max_new_tokens)

    def stream(self, prompt: str, max_new_tokens: int) -> Iterator[str]:
        streamer = TextIteratorStreamer(
            self.bundle.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        encoded = self.bundle.tokenizer(prompt, return_tensors="pt")
        encoded = {key: value.to(self.bundle.device) for key, value in encoded.items()}
        errors: list[Exception] = []

        def run_generation() -> None:
            try:
                with self._model_lock, torch.inference_mode():
                    self.bundle.model.generate(
                        **encoded,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        pad_token_id=self.bundle.tokenizer.pad_token_id,
                        streamer=streamer,
                    )
            except Exception as exc:  # noqa: BLE001 - relay thread errors to iterator
                errors.append(exc)
                streamer.end()

        worker = Thread(target=run_generation, name="model-stream", daemon=True)
        worker.start()
        yield from streamer
        worker.join()
        if errors:
            raise errors[0]
