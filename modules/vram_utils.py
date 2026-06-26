import gc
import torch
from config import DEVICE


def clear_vram():
    """Call between loading different models to free GPU memory."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def get_vram_usage() -> str:
    """Return current VRAM usage as a human-readable string."""
    if not torch.cuda.is_available():
        return "No CUDA GPU detected"
    used = torch.cuda.memory_allocated() / 1e9
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    return f"{used:.1f} GB used / {total:.1f} GB total"


def is_vram_safe(required_gb: float, buffer_gb: float = 1.0) -> bool:
    """Return True if enough VRAM is free before loading a model."""
    if not torch.cuda.is_available():
        return True
    free = (
        torch.cuda.get_device_properties(0).total_memory
        - torch.cuda.memory_allocated()
    ) / 1e9
    return free >= (required_gb + buffer_gb)
