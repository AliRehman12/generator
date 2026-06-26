"""
MusePose wrapper — optional full-body animation.

Requires ~12 GB VRAM. Must be run in a fresh Colab session
with no other models loaded.
"""

import os
import subprocess
import sys
from config import MUSEPOSE_DIR, DEVICE
from modules.vram_utils import clear_vram, is_vram_safe, get_vram_usage

_MUSEPOSE_VRAM_GB = 12.0


def animate_body(
    reference_image_path: str,
    driving_video_path: str,
    output_path: str,
    width: int = 512,
    height: int = 768,
) -> str:
    """
    Animate a full-body avatar using MusePose.

    Args:
        reference_image_path : Full-body or half-body photo of the person.
        driving_video_path   : Reference motion video (gesture / dance).
        output_path          : Where to save the output .mp4.
        width / height       : Output resolution (keep 512×768 for T4 safety).

    Returns:
        Path to the animated video.
    """
    if not os.path.exists(MUSEPOSE_DIR):
        raise FileNotFoundError(
            "Model weights not found. Re-run Cell 3 (download weights) in the notebook."
        )

    if not is_vram_safe(required_gb=_MUSEPOSE_VRAM_GB):
        raise RuntimeError(
            f"MusePose needs 12 GB free VRAM. Current usage: {get_vram_usage()}. "
            "Unload all other models with their unload_models() calls first, "
            "or restart the Colab runtime before running body animation."
        )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    config_path = os.path.join(MUSEPOSE_DIR, "configs/test/test_stage2.yaml")
    cmd = [
        sys.executable,
        os.path.join(MUSEPOSE_DIR, "pose2vid.py"),
        "--config", config_path,
        "--ref_image_path", reference_image_path,
        "--ref_video_path", driving_video_path,
        "--output_path", output_path,
        "--width", str(width),
        "--height", str(height),
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=MUSEPOSE_DIR,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "Generation timed out after 20 minutes. "
            "Try a shorter driving video or lower output resolution."
        )

    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "out of memory" in stderr:
            raise RuntimeError(
                "GPU ran out of memory. Try switching to 256 resolution, or restart "
                "the Colab runtime and run the voice and avatar steps in separate sessions."
            )
        raise RuntimeError(f"MusePose failed:\n{result.stderr}")

    if not os.path.exists(output_path):
        raise RuntimeError("MusePose ran but output file not found.")

    return output_path
