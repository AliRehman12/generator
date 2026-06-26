"""
Download all model checkpoints needed by the avatar pipeline.

Idempotent — skips files that already exist.
Run this as: python setup/download_weights.py
"""

import os
import subprocess


def download_if_missing(url: str, dest_path: str):
    if os.path.exists(dest_path):
        print(f"  ✓  Already exists: {dest_path}")
        return
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    print(f"  ↓  Downloading: {os.path.basename(dest_path)}")
    subprocess.run(["wget", "-q", "--show-progress", "-O", dest_path, url], check=True)


# ---------------------------------------------------------------------------
# SadTalker checkpoints
# ---------------------------------------------------------------------------
print("\n=== SadTalker checkpoints ===")
SADTALKER_CKPT_BASE = (
    "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc"
)
sadtalker_files = [
    "SadTalker_V0.0.2_256.safetensors",
    "SadTalker_V0.0.2_512.safetensors",
    "mapping_00109-model.pth.tar",
    "mapping_00229-model.pth.tar",
    "facevid2vid_00189-model.pth.tar",
    "auido2exp_00300-model.pth",
    "auido2pose_00140-model.pth",
    "wav2lip.pth",
    "shape_predictor_68_face_landmarks.dat",
    "BFM_Fitting.zip",
    "hub.zip",
]
for fname in sadtalker_files:
    download_if_missing(
        f"{SADTALKER_CKPT_BASE}/{fname}",
        f"/content/SadTalker/checkpoints/{fname}",
    )

# Unzip BFM and hub archives if needed
for archive in ["BFM_Fitting.zip", "hub.zip"]:
    archive_path = f"/content/SadTalker/checkpoints/{archive}"
    extracted_dir = archive_path.replace(".zip", "")
    if os.path.exists(archive_path) and not os.path.exists(extracted_dir):
        print(f"  📦 Extracting {archive}…")
        subprocess.run(
            ["unzip", "-q", archive_path, "-d", "/content/SadTalker/checkpoints/"],
            check=True,
        )

# ---------------------------------------------------------------------------
# OpenVoice v2 checkpoints (stored in Git LFS)
# ---------------------------------------------------------------------------
print("\n=== OpenVoice v2 checkpoints ===")
if os.path.exists("/content/OpenVoice"):
    print("  Pulling LFS objects for OpenVoice v2…")
    subprocess.run(["git", "lfs", "install"], cwd="/content/OpenVoice", check=True)
    subprocess.run(["git", "lfs", "pull"], cwd="/content/OpenVoice", check=True)
    print("  ✓  OpenVoice v2 weights ready.")
else:
    print("  ✗  /content/OpenVoice not found — run install.sh first.")

# ---------------------------------------------------------------------------
# MusePose checkpoints (Hugging Face)
# ---------------------------------------------------------------------------
print("\n=== MusePose checkpoints ===")
musepose_ckpt_dir = "/content/MusePose/pretrained_weights"
if not os.path.exists(musepose_ckpt_dir):
    os.makedirs(musepose_ckpt_dir, exist_ok=True)
    print("  Downloading MusePose weights from Hugging Face (this takes a while)…")
    try:
        subprocess.run(
            [
                "python", "-c",
                (
                    "from huggingface_hub import snapshot_download; "
                    "snapshot_download('TMElyralab/MusePose', "
                    "local_dir='/content/MusePose/pretrained_weights')"
                ),
            ],
            check=True,
        )
        print("  ✓  MusePose weights ready.")
    except subprocess.CalledProcessError:
        print(
            "  ✗  MusePose download failed. "
            "You can manually download from https://huggingface.co/TMElyralab/MusePose"
        )
else:
    print(f"  ✓  Already exists: {musepose_ckpt_dir}")

print("\n=== All weights downloaded. You are ready to launch the app. ===\n")
