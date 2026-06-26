#!/bin/bash
# Idempotent environment setup script for Google Colab T4.
set -e

echo "=== [1/8] Checking Python version ==="
PY_MINOR=$(python -c "import sys; print(sys.version_info.minor)")
python -c "
import sys
v = sys.version_info
print(f'    Python {v.major}.{v.minor}.{v.micro}')
if v >= (3, 12):
    print('    ⚠️  Python 3.12 — voice cloning DISABLED (need runtime 2025.07)')
    print('    ✅  Kokoro TTS + SadTalker will still work')
else:
    print('    ✅ Python version OK for voice cloning')
"

echo "=== [2/8] Installing system dependencies ==="
apt-get install -y ffmpeg libsndfile1 cmake build-essential > /dev/null 2>&1
echo "    ffmpeg + libsndfile1 ready."

echo "=== [3/8] Cloning SadTalker ==="
if [ ! -d "/content/SadTalker" ]; then
  git clone https://github.com/OpenTalker/SadTalker.git /content/SadTalker
fi
echo "    SadTalker ready."

echo "=== [4/8] Cloning OpenVoice v2 ==="
if [ ! -d "/content/OpenVoice" ]; then
  git clone https://github.com/myshell-ai/OpenVoice.git /content/OpenVoice
fi
echo "    OpenVoice ready."

echo "=== [5/8] Cloning MusePose ==="
if [ ! -d "/content/MusePose" ]; then
  git clone https://github.com/TMElyralab/MusePose.git /content/MusePose
fi
echo "    MusePose ready."

echo "=== [6/8] Installing Python packages ==="
# Colab pre-installs gradio 5.x — force downgrade to 4.44
pip uninstall -y gradio 2>/dev/null || true
pip install -q "setuptools<82" "huggingface_hub==0.25.2"
pip install -q --force-reinstall "gradio==4.44.0"

pip install -q \
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

echo "=== [7/8] Installing MeloTTS (voice cloning — Python 3.11 only) ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/install_melo.py" || true

echo "=== [8/8] Skipping repo requirements.txt (avoids numpy rebuild conflicts on Colab) ==="
echo "    Core deps already installed above."

# Keep huggingface_hub compatible with Gradio 4.44
pip install -q "huggingface_hub==0.25.2"

echo ""
if [ "$PY_MINOR" -ge 12 ]; then
  echo "=== Setup done (limited mode on Python 3.12) ==="
  echo "    ✅ Kokoro preset voices + SadTalker avatar video"
  echo "    ❌ Voice cloning — switch to runtime 2025.07 to enable"
else
  echo "=== Setup complete. Run download_weights.py next. ==="
fi
