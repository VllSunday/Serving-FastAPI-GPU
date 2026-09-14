from __future__ import annotations

import time

import torch

from app.model.loader import ModelBundle
from app.model.prompting import format_prompts


def _move_to_device(encoded: dict, device: str) -> dict:
    return {key: value.to(device) for key, value in encoded.items()}


def generate_one(
    bundle: ModelBundle,
    prompt: str,
    max_new_tokens: int,
) -> tuple[str, float]:
    """Форматирует один prompt, запускает модель и декодирует completion."""
    # Подготовка input не входит в inference_ms: здесь только tokenizer и device copy.
    formatted, uses_chat_template = format_prompts(bundle.tokenizer, [prompt])
    encoded = bundle.tokenizer(
        formatted[0],
        return_tensors="pt",
        add_special_tokens=not uses_chat_template,
    )
    encoded = _move_to_device(encoded, bundle.device)

    # Таймер охватывает ровно model.generate().
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
    """Собирает prompts в один tensor batch и возвращает тексты в том же порядке."""
    # padding делает прямоугольный tensor [batch_size, max_prompt_length].
    formatted, uses_chat_template = format_prompts(bundle.tokenizer, prompts)
    encoded = bundle.tokenizer(
        formatted,
        return_tensors="pt",
        padding=True,
        truncation=True,
        add_special_tokens=not uses_chat_template,
    )
    encoded = _move_to_device(encoded, bundle.device)

    # Это время всего batch-вызова, а не сумма и не среднее по prompt.
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
