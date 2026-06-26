"""
Kokoro TTS fallback.

Used when the user wants speech generation without voice cloning.
Runs on CPU — no VRAM needed.
Available preset voices: af_heart, af_bella, am_adam, bf_emma, bm_george
"""

import os
import numpy as np
import soundfile as sf
from config import TEMP_DIR


def generate_speech_kokoro(
    text: str,
    output_path: str,
    voice: str = "af_heart",
    speed: float = 1.0,
) -> str:
    """
    Generate speech using Kokoro TTS (no voice cloning, preset voices).

    Args:
        text        : The script to synthesise.
        output_path : Where to save the output .wav file.
        voice       : One of af_heart | af_bella | am_adam | bf_emma | bm_george
        speed       : Speaking speed multiplier (0.7 – 1.3 recommended).

    Returns:
        Path to the generated .wav file.
    """
    from kokoro import KPipeline

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    else:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, os.path.basename(output_path))

    pipeline = KPipeline(lang_code="a")
    samples, sample_rate = [], 24000

    for _, _, audio in pipeline(text, voice=voice, speed=speed):
        samples.append(audio)

    combined = np.concatenate(samples)
    sf.write(output_path, combined, sample_rate)
    return output_path
