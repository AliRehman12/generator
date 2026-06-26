"""
SadTalker wrapper.

Generates a talking-head video from a face photo + driving audio.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from config import (
    DEVICE,
    SADTALKER_DIR,
    SADTALKER_CHECKPOINT_DIR,
    TEMP_DIR,
    DEFAULT_STILL_MODE,
    DEFAULT_PREPROCESS,
    DEFAULT_ENHANCER,
    DEFAULT_EXPRESSION_SCALE,
    DEFAULT_SIZE,
    USE_HALF_PRECISION,
)
from modules.vram_utils import clear_vram, is_vram_safe, get_vram_usage


def generate_talking_head(
    source_image_path: str,
    audio_path: str,
    output_dir: str,
    still_mode: bool = DEFAULT_STILL_MODE,
    preprocess: str = DEFAULT_PREPROCESS,
    enhancer: str = DEFAULT_ENHANCER,
    expression_scale: float = DEFAULT_EXPRESSION_SCALE,
    size: int = DEFAULT_SIZE,
    pose_style: int = 0,
) -> str:
    """
    Generate a talking-head video using SadTalker.

    Args:
        source_image_path : Path to input face image (JPG/PNG, frontal).
        audio_path        : Path to driving audio (.wav or .mp3).
        output_dir        : Directory to save the output video.
        still_mode        : Reduce head movement when True.
        preprocess        : "crop" works best for most photos.
        enhancer          : "gfpgan" | "RestoreFormer" | None
        expression_scale  : 0.5 – 2.0 (default 1.0).
        size              : 256 (faster) or 512 (higher quality, more VRAM).
        pose_style        : 0–45, controls head pose variation.

    Returns:
        Absolute path to the generated .mp4 video.
    """
    if not os.path.exists(SADTALKER_DIR):
        raise FileNotFoundError(
            "Model weights not found. Re-run Cell 3 (download weights) in the notebook."
        )

    required_gb = 7.0 if size == 256 else 10.0
    if not is_vram_safe(required_gb=required_gb):
        raise RuntimeError(
            f"GPU ran out of memory. Try switching to 256 resolution, or restart the "
            f"Colab runtime and run the voice and avatar steps in separate sessions. "
            f"Current VRAM: {get_vram_usage()}"
        )

    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        sys.executable,
        os.path.join(SADTALKER_DIR, "inference.py"),
        "--driven_audio", audio_path,
        "--source_image", source_image_path,
        "--result_dir", output_dir,
        "--preprocess", preprocess,
        "--expression_scale", str(expression_scale),
        "--size", str(size),
        "--pose_style", str(pose_style),
    ]

    if still_mode:
        cmd.append("--still")

    if enhancer and enhancer.lower() != "none":
        cmd += ["--enhancer", enhancer]

    try:
        result = subprocess.run(
            cmd,
            cwd=SADTALKER_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "Generation timed out after 10 minutes. "
            "Try a shorter audio clip or 256 resolution."
        )

    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "no face" in stderr or "face not" in stderr:
            raise RuntimeError(
                "No face detected in your photo. Use a clear, frontal photo with "
                "good lighting and no heavy filters."
            )
        if "out of memory" in stderr or "cuda" in stderr and "memory" in stderr:
            raise RuntimeError(
                "GPU ran out of memory. Try switching to 256 resolution, or restart "
                "the Colab runtime and run the voice and avatar steps in separate sessions."
            )
        raise RuntimeError(f"SadTalker failed:\n{result.stderr}")

    output_files = list(Path(output_dir).glob("*.mp4"))
    if not output_files:
        raise RuntimeError("SadTalker ran but produced no output video.")

    latest = max(output_files, key=lambda f: f.stat().st_mtime)
    return str(latest)


def unload_models():
    """No persistent state in this module — just clear VRAM."""
    clear_vram()
