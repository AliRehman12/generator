# AI Avatar Video Generator

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/avatar_pipeline/blob/main/colab_main.ipynb)

Upload a face photo and a voice sample, type your script, and get a realistic talking-head video back in minutes — all running free on a Google Colab T4 GPU. Powered by **SadTalker** for facial animation, **OpenVoice v2** for real-time voice cloning, **Kokoro TTS** as a lightweight fallback, and optionally **MusePose** for full-body animation.

---

## Hardware requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| GPU | NVIDIA T4 (16 GB VRAM) | NVIDIA A100 (40 GB) |
| RAM | 12 GB | 16 GB |
| Storage | 20 GB free | 30 GB free |
| Runtime | Google Colab free tier | Colab Pro |

> Apple M1/M2 is supported for **voice generation only** (MPS backend). SadTalker and MusePose require CUDA.

---

## 5-step setup in Colab

Open `colab_main.ipynb` in Google Colab and run the cells in order:

1. **Cell 1 — Mount Google Drive**
   Connects your Drive so outputs are saved permanently to `MyDrive/AvatarOutput/`.

2. **Cell 2 — Clone repo + install dependencies**
   Clones this repo and runs `setup/install.sh` (ffmpeg, all Python packages, SadTalker, OpenVoice, MusePose).
   Takes ~5 minutes on first run.

3. **Cell 3 — Download model weights**
   Downloads SadTalker checkpoints, OpenVoice v2 weights (via Git LFS), and MusePose weights (~8 GB total).
   Skips files that are already present — safe to re-run after runtime restarts.

4. **Cell 4 — Verify GPU**
   Confirms CUDA is available, prints GPU name and VRAM. Warns if VRAM < 14 GB.

5. **Cell 5 — Launch the app**
   Starts the Gradio server. A public URL (`https://abc123.gradio.live`) is printed — click it to open the UI.

---

## How to use each tab

### Tab 1 — Voice Setup
1. Upload a voice sample (5–30 seconds, WAV/MP3) **or** record directly from your microphone.
2. Type your script in the text box.
3. Choose language and speaking speed.
4. Keep **"Use voice cloning"** checked to clone your voice, or uncheck it and pick a Kokoro preset voice.
5. Click **Generate audio preview** and listen before proceeding.

### Tab 2 — Generate Avatar Video
1. Upload a clear, frontal face photo.
2. The audio from Tab 1 auto-fills — or upload a separate audio file.
3. Expand **Advanced settings** to tune expression intensity, face enhancer, resolution, and pose style.
4. Click **Generate talking avatar video**.
5. Click **Save to Google Drive** to keep the output permanently.

### Tab 3 — Body Animation (optional)
> ⚠️ Restart the Colab runtime before using this tab — MusePose needs ~12 GB free VRAM.

1. Upload a full-body or half-body photo.
2. Upload a reference motion video (dance or gesture clip).
3. Set output resolution (512×768 recommended for T4).
4. Click **Animate body**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **GPU ran out of memory** | Switch to 256 resolution in Advanced settings, or restart the runtime and run voice + avatar in separate sessions. |
| **No face detected** | Use a clear, well-lit frontal photo. Remove sunglasses, heavy filters, or extreme angles. |
| **Audio too short** | Record or upload at least 5 seconds for voice cloning. |
| **Drive not mounted** | Re-run Cell 1 and follow the Google authentication prompt. |
| **Weights missing** | Re-run Cell 3 (`download_weights.py`). |
| **App URL not appearing** | Interrupt Cell 5 and re-run it. |
| **MusePose hangs** | Restart the runtime (do NOT load voice/avatar models before running Tab 3). |

---

## Photo tips for best results

- Use a **clear, frontal shot** with the face centred.
- Good, even **lighting** — avoid harsh shadows or backlighting.
- **No sunglasses** or heavy accessories covering the face.
- A **plain or blurred background** reduces distractions.
- Resolution of at least **512×512 px** recommended.
- Avoid heavily filtered or heavily compressed images (e.g. small JPEG).

---

## Voice cloning tips

- Record in a **quiet room** — background noise degrades quality significantly.
- Speak **naturally** at your normal pace; don't slow down artificially.
- **10–30 seconds** of clean speech works best.
- Avoid music, echoes, or multiple speakers in the same clip.
- WAV or FLAC files give cleaner results than compressed MP3.

---

## Project structure

```
avatar_pipeline/
├── colab_main.ipynb        ← Colab notebook (run this)
├── app.py                  ← Gradio app entry point
├── config.py               ← All paths and model settings
├── modules/
│   ├── vram_utils.py       ← VRAM management
│   ├── voice_module.py     ← OpenVoice v2 wrapper
│   ├── tts_module.py       ← Kokoro TTS fallback
│   ├── talking_head.py     ← SadTalker wrapper
│   └── body_module.py      ← MusePose wrapper
├── setup/
│   ├── install.sh          ← Environment setup
│   └── download_weights.py ← Checkpoint downloads
├── requirements.txt
└── README.md
```

---

## Credits

- [SadTalker](https://github.com/OpenTalker/SadTalker) — talking-head generation
- [OpenVoice v2](https://github.com/myshell-ai/OpenVoice) — voice cloning
- [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M) — lightweight TTS fallback
- [MusePose](https://github.com/TMElyralab/MusePose) — body animation
- [Gradio](https://gradio.app) — UI framework
