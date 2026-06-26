#!/bin/bash
# Idempotent environment setup script for Google Colab T4.
# Safe to run multiple times — skips steps that are already done.
set -e

echo "=== [1/8] Checking Python version ==="
python -c "
import sys
v = sys.version_info
print(f'    Python {v.major}.{v.minor}.{v.micro}')
if v >= (3, 12):
    print('    ⚠️  Python 3.12 — voice cloning needs runtime version 2025.07 (Python 3.11)')
else:
    print('    ✅ Python version OK for MeloTTS')
"

echo "=== [2/8] Installing system dependencies ==="
apt-get install -y ffmpeg libsndfile1 cmake build-essential > /dev/null 2>&1
echo "    ffmpeg + libsndfile1 ready."

echo "=== [3/8] Cloning SadTalker ==="
if [ ! -d "/content/SadTalker" ]; then
  git clone https://github.com/OpenTalker/SadTalker.git /content/SadTalker
  echo "    SadTalker cloned."
else
  echo "    SadTalker already present — skipping clone."
fi

echo "=== [4/8] Cloning OpenVoice v2 ==="
if [ ! -d "/content/OpenVoice" ]; then
  git clone https://github.com/myshell-ai/OpenVoice.git /content/OpenVoice
  echo "    OpenVoice cloned."
else
  echo "    OpenVoice already present — skipping clone."
fi

echo "=== [5/8] Cloning MusePose ==="
if [ ! -d "/content/MusePose" ]; then
  git clone https://github.com/TMElyralab/MusePose.git /content/MusePose
  echo "    MusePose cloned."
else
  echo "    MusePose already present — skipping clone."
fi

echo "=== [6/8] Installing Python packages ==="
# Gradio 4.44 requires HfFolder, removed in huggingface_hub >= 0.26
pip install -q "huggingface_hub>=0.19.3,<0.26.0"

pip install -q \
  gradio==4.44.0 \
  torch torchvision torchaudio \
  transformers accelerate \
  openai-whisper \
  "kokoro>=0.9.4" \
  soundfile librosa \
  gfpgan \
  basicsr facexlib realesrgan \
  imageio "imageio-ffmpeg" \
  scikit-image scipy \
  yacs pyyaml \
  face-alignment \
  xformers

echo "=== [7/8] Installing MeloTTS (voice cloning) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/install_melo.py" || echo "    ⚠️  MeloTTS failed — use Kokoro voices or switch to runtime 2025.07"

echo "=== [8/8] Installing repo-specific requirements ==="
pip install -q -r /content/SadTalker/requirements.txt || true
pip install -q -r /content/OpenVoice/requirements.txt || true

# Re-pin huggingface_hub — OpenVoice/SadTalker may upgrade it and break Gradio
pip install -q "huggingface_hub>=0.19.3,<0.26.0"

echo ""
echo "=== Setup complete. Run download_weights.py next. ==="
