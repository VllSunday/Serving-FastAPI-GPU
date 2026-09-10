from __future__ import annotations

from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.config import settings


@dataclass
class ModelBundle:
    model: AutoModelForCausalLM
    tokenizer: AutoTokenizer
    device: str
    gpu_name: str | None
    model_name: str


def resolve_device(requested: str) -> str:
    requested = (requested or "auto").strip().lower()
    cuda_ok = torch.cuda.is_available()

    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        if cuda_ok:
            return "cuda"
        print("WARNING: DEVICE=cuda, but CUDA is unavailable. Falling back to CPU.")
        return "cpu"
    return "cuda" if cuda_ok else "cpu"


def load_model() -> ModelBundle:
    device = resolve_device(settings.device)
    model_name = settings.model_name
    gpu_name = torch.cuda.get_device_name(0) if device == "cuda" else None

    print(f"Device: {device}")
    if gpu_name:
        print(f"GPU: {gpu_name}")
    print(f"Model: {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # GPT-2 family has no pad token. Left padding matters for decoder-only batching.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch_dtype)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch_dtype)
    model.to(device)
    model.eval()

    if tokenizer.pad_token_id is not None:
        model.config.pad_token_id = tokenizer.pad_token_id

    return ModelBundle(
        model=model,
        tokenizer=tokenizer,
        device=device,
        gpu_name=gpu_name,
        model_name=model_name,
    )
