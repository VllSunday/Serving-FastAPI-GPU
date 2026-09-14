from __future__ import annotations

import time

import torch

from app.model.loader import ModelBundle


def _move_to_device(encoded: dict, device: str) -> dict:
    return {key: value.to(device) for key, value in encoded.items()}


def generate_one(
    bundle: ModelBundle,
    prompt: str,
    max_new_tokens: int,
) -> tuple[str, float]:
    encoded = bundle.tokenizer(prompt, return_tensors="pt")
    encoded = _move_to_device(encoded, bundle.device)

    started = time.perf_counter()
    with torch.inference_mode():
        output_ids = bundle.model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=bundle.tokenizer.pad_token_id,
        )
    latency_ms = (time.perf_counter() - started) * 1000
    prompt_length = encoded["input_ids"].shape[1]
    text = bundle.tokenizer.decode(
        output_ids[0, prompt_length:],
        skip_special_tokens=True,
    )
    return text, latency_ms


def generate_batch(
    bundle: ModelBundle,
    prompts: list[str],
    max_new_tokens: int,
) -> tuple[list[str], float]:
    encoded = bundle.tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
    )
    encoded = _move_to_device(encoded, bundle.device)

    started = time.perf_counter()
    with torch.inference_mode():
        output_ids = bundle.model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=bundle.tokenizer.pad_token_id,
        )
    latency_ms = (time.perf_counter() - started) * 1000
    prompt_length = encoded["input_ids"].shape[1]
    texts = bundle.tokenizer.batch_decode(
        output_ids[:, prompt_length:],
        skip_special_tokens=True,
    )
    return texts, latency_ms
