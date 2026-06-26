import torch
import os

# ---------------------------------------------------------------------------
# Device detection
# ---------------------------------------------------------------------------
DEVICE = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
USE_HALF_PRECISION = DEVICE == "cuda"  # fp16 on GPU, fp32 on CPU/MPS

# ---------------------------------------------------------------------------
# Directory paths (Colab layout)
# ---------------------------------------------------------------------------
CONTENT_DIR = "/content"
DRIVE_OUTPUT_DIR = "/content/drive/MyDrive/AvatarOutput"
SADTALKER_DIR = "/content/SadTalker"
OPENVOICE_DIR = "/content/OpenVoice"
MUSEPOSE_DIR = "/content/MusePose"
KOKORO_DIR = "/content/Kokoro"

TEMP_DIR = "/content/avatar_temp"

# ---------------------------------------------------------------------------
# Model checkpoint paths
# ---------------------------------------------------------------------------
SADTALKER_CHECKPOINT_DIR = "/content/SadTalker/checkpoints"
SADTALKER_CONFIG_DIR = "/content/SadTalker/src/config"
OPENVOICE_CHECKPOINT_DIR = "/content/OpenVoice/checkpoints_v2"

# ---------------------------------------------------------------------------
# Generation defaults
# ---------------------------------------------------------------------------
DEFAULT_STILL_MODE = False          # True = less head movement
DEFAULT_PREPROCESS = "crop"         # "crop" | "full" | "extcrop" | "extfull"
DEFAULT_ENHANCER = "gfpgan"         # "gfpgan" | "RestoreFormer" | None
DEFAULT_EXPRESSION_SCALE = 1.0      # 0.5 – 2.0
DEFAULT_SIZE = 256                  # 256 (faster) or 512 (higher quality, more VRAM)
