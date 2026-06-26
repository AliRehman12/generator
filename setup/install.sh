#!/bin/bash
# Idempotent environment setup script for Google Colab T4.
# Safe to run multiple times — skips steps that are already done.
set -e

echo "=== [1/7] Installing system dependencies ==="
apt-get install -y ffmpeg libsndfile1 cmake build-essential > /dev/null 2>&1
echo "    ffmpeg + libsndfile1 ready."

echo "=== [2/7] Cloning SadTalker ==="
if [ ! -d "/content/SadTalker" ]; then
  git clone https://github.com/OpenTalker/SadTalker.git /content/SadTalker
  echo "    SadTalker cloned."
else
  echo "    SadTalker already present — skipping clone."
fi

echo "=== [3/7] Cloning OpenVoice v2 ==="
if [ ! -d "/content/OpenVoice" ]; then
  git clone https://github.com/myshell-ai/OpenVoice.git /content/OpenVoice
  echo "    OpenVoice cloned."
else
  echo "    OpenVoice already present — skipping clone."
fi

echo "=== [4/7] Cloning MusePose ==="
if [ ! -d "/content/MusePose" ]; then
  git clone https://github.com/TMElyralab/MusePose.git /content/MusePose
  echo "    MusePose cloned."
else
  echo "    MusePose already present — skipping clone."
fi

echo "=== [5/7] Installing Python packages ==="
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

echo "=== [6/7] Installing MeloTTS from GitHub ==="
# MeloTTS is not on PyPI — install deps first for Python 3.12
pip install -q \
  cn2an pypinyin inflect unidecode eng-to-ipa pydub \
  "gruut[de,es,fr]==2.2.3" \
  nltk

pip install -q --no-build-isolation git+https://github.com/myshell-ai/MeloTTS.git

python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True)" 2>/dev/null || true

echo "=== [7/7] Installing repo-specific requirements ==="
pip install -q -r /content/SadTalker/requirements.txt || true
pip install -q -r /content/OpenVoice/requirements.txt || true

# Re-pin huggingface_hub — OpenVoice/SadTalker may upgrade it and break Gradio
pip install -q "huggingface_hub>=0.19.3,<0.26.0"

echo ""
echo "=== Setup complete. Run download_weights.py next. ==="
