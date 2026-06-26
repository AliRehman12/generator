"""
OpenVoice v2 wrapper.

Tasks:
  - extract_speaker_embedding  : extract timbre from a reference audio clip
  - clone_voice_to_audio       : synthesise speech in the cloned voice
  - unload_models              : release GPU memory
"""

import os
import sys
import torch
from config import (
    DEVICE,
    OPENVOICE_DIR,
    OPENVOICE_CHECKPOINT_DIR,
    TEMP_DIR,
    USE_HALF_PRECISION,
)
from modules.vram_utils import clear_vram

sys.path.insert(0, OPENVOICE_DIR)

_tone_color_converter = None


def _load_models():
    global _tone_color_converter
    if _tone_color_converter is not None:
        return
    from openvoice.api import ToneColorConverter

    clear_vram()
    ckpt_path = os.path.join(OPENVOICE_CHECKPOINT_DIR, "converter")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            "Model weights not found. Re-run Cell 3 (download weights) in the notebook."
        )
    _tone_color_converter = ToneColorConverter(
        f"{ckpt_path}/config.json", device=DEVICE
    )
    _tone_color_converter.load_ckpt(f"{ckpt_path}/checkpoint.pth")


def extract_speaker_embedding(reference_audio_path: str) -> str:
    """
    Extract speaker timbre from a reference audio clip (5–30 sec recommended).
    Returns path to the saved .pth embedding file.
    """
    import soundfile as sf

    # Validate minimum duration
    data, sr = sf.read(reference_audio_path)
    duration = len(data) / sr
    if duration < 2.0:
        raise ValueError(
            "Audio clip is too short for voice cloning. "
            "Record or upload at least 5 seconds of your voice."
        )

    _load_models()
    from openvoice import se_extractor

    os.makedirs(TEMP_DIR, exist_ok=True)
    embedding_path = os.path.join(TEMP_DIR, "speaker_embedding.pth")
    target_se, _ = se_extractor.get_se(
        reference_audio_path, _tone_color_converter, vad=True
    )
    torch.save(target_se, embedding_path)
    return embedding_path


def clone_voice_to_audio(
    text: str,
    speaker_embedding_path: str,
    output_path: str,
    language: str = "EN",
    speed: float = 1.0,
) -> str:
    """
    Generate speech in the cloned voice.
    Returns path to the output .wav file.
    """
    _load_models()
    from melo.api import TTS

    os.makedirs(os.path.dirname(output_path) or TEMP_DIR, exist_ok=True)

    tts_model = TTS(language=language, device=DEVICE)
    speaker_ids = tts_model.hps.data.spk2id
    speaker_key = language.lower().replace("_", "-")
    speaker_id = next(
        (v for k, v in speaker_ids.items() if speaker_key in k.lower()),
        list(speaker_ids.values())[0],
    )

    tmp_tts_path = os.path.join(TEMP_DIR, "tts_raw.wav")
    tts_model.tts_to_file(text, speaker_id, tmp_tts_path, speed=speed)

    target_se = torch.load(speaker_embedding_path, map_location=DEVICE)
    source_se_path = os.path.join(
        OPENVOICE_CHECKPOINT_DIR, "base_speakers/ses/en-newest.pth"
    )
    if not os.path.exists(source_se_path):
        raise FileNotFoundError(
            "Model weights not found. Re-run Cell 3 (download weights) in the notebook."
        )
    source_se = torch.load(source_se_path, map_location=DEVICE)

    _tone_color_converter.convert(
        audio_src_path=tmp_tts_path,
        src_se=source_se,
        tgt_se=target_se,
        output_path=output_path,
        message="@MyShell",
    )
    return output_path


def unload_models():
    global _tone_color_converter
    _tone_color_converter = None
    clear_vram()
