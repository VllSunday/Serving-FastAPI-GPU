from __future__ import annotations

import asyncio
from threading import Thread

import torch
from transformers import TextIteratorStreamer

from app.model.loader import ModelBundle


def _run_generate(bundle: ModelBundle, encoded: dict, max_new_tokens: int, streamer) -> None:
    try:
        with torch.inference_mode():
            bundle.model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=bundle.tokenizer.pad_token_id,
                streamer=streamer,
            )
    except Exception:
        streamer.end()
        raise


async def stream_generate(bundle: ModelBundle, prompt: str, max_new_tokens: int):
    """Yield growing decoded text. Generation runs in a worker thread."""
    # TODO(student):
    # stream tokens to the client before the full sequence is ready
    # do not block the event loop with model.generate()
    streamer = TextIteratorStreamer(
        bundle.tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )
    encoded = bundle.tokenizer(prompt, return_tensors="pt")
    encoded = {key: value.to(bundle.device) for key, value in encoded.items()}

    worker = Thread(
        target=_run_generate,
        args=(bundle, encoded, max_new_tokens, streamer),
        daemon=True,
    )
    worker.start()

    accumulated = ""
    iterator = iter(streamer)
    while True:
        piece = await asyncio.to_thread(_next_chunk, iterator)
        if piece is None:
            break
        if not piece:
            continue
        accumulated += piece
        yield accumulated + "\n"

    await asyncio.to_thread(worker.join)


def _next_chunk(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None
