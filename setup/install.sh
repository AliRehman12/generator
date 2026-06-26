#!/bin/bash
# Idempotent environment setup script for Google Colab T4.
# Safe to run multiple times — skips steps that are already done.
set -e

echo "=== [1/6] Installing system dependencies ==="
apt-get install -y ffmpeg libsndfile1 > /dev/null 2>&1
echo "    ffmpeg + libsndfile1 ready."

echo "=== [2/6] Cloning SadTalker ==="
if [ ! -d "/content/SadTalker" ]; then
  git clone https://github.com/OpenTalker/SadTalker.git /content/SadTalker
  echo "    SadTalker cloned."
else
  echo "    SadTalker already present — skipping clone."
fi

echo "=== [3/6] Cloning OpenVoice v2 ==="
if [ ! -d "/content/OpenVoice" ]; then
  git clone https://github.com/myshell-ai/OpenVoice.git /content/OpenVoice
  echo "    OpenVoice cloned."
else
  echo "    OpenVoice already present — skipping clone."
fi

echo "=== [4/6] Cloning MusePose ==="
if [ ! -d "/content/MusePose" ]; then
  git clone https://github.com/TMElyralab/MusePose.git /content/MusePose
  echo "    MusePose cloned."
else
  echo "    MusePose already present — skipping clone."
fi

echo "=== [5/6] Installing Python packages ==="
pip install -q \
  gradio==4.44.0 \
  torch torchvision torchaudio \
  transformers accelerate \
  openai-whisper \
  "kokoro>=0.9.4" \
  soundfile librosa \
  gfpgan \
  basicsr facexlib realesrgan \
  melo-tts \
  imageio "imageio-ffmpeg" \
  scikit-image scipy \
  yacs pyyaml \
  dlib face-alignment \
  xformers

echo "=== [6/6] Installing repo-specific requirements ==="
pip install -q -r /content/SadTalker/requirements.txt
pip install -q -r /content/OpenVoice/requirements.txt

echo ""
echo "=== Setup complete. Run download_weights.py next. ==="
