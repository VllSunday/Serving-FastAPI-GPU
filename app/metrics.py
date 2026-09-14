from __future__ import annotations

import torch


def gpu_snapshot(device: str) -> dict:
    """Снимок VRAM через PyTorch; utilization доступен не на всех сборках."""
    if device != "cuda" or not torch.cuda.is_available():
        return {
            "device": device,
            "gpu": None,
            "allocated_bytes": 0,
            "reserved_bytes": 0,
            "allocated_mb": 0.0,
            "reserved_mb": 0.0,
            "utilization_pct": None,
        }

    allocated = torch.cuda.memory_allocated()
    reserved = torch.cuda.memory_reserved()
    utilization = None
    try:
        utilization = torch.cuda.utilization()
    except (AttributeError, RuntimeError):
        utilization = None

    return {
        "device": "cuda",
        "gpu": torch.cuda.get_device_name(0),
        "allocated_bytes": allocated,
        "reserved_bytes": reserved,
        "allocated_mb": round(allocated / (1024**2), 2),
        "reserved_mb": round(reserved / (1024**2), 2),
        "utilization_pct": utilization,
    }
