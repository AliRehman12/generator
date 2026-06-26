"""
Download all model checkpoints needed by the avatar pipeline.

Idempotent — skips files that already exist.
Run this as: python setup/download_weights.py
"""

import os
import subprocess
import zipfile
import urllib.request


def download_if_missing(url: str, dest_path: str):
    if os.path.exists(dest_path):
        print(f"  ✓  Already exists: {dest_path}")
        return
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    print(f"  ↓  Downloading: {os.path.basename(dest_path)}")
    subprocess.run(["wget", "-q", "--show-progress", "-O", dest_path, url], check=True)


def _patch_basicsr():
    """basicsr imports torchvision.transforms.functional_tensor which was removed.
    Patch the file so SadTalker can load gfpgan."""
    target = "/usr/local/lib/python3.11/dist-packages/basicsr/data/degradations.py"
    if not os.path.exists(target):
        return
    with open(target, "r") as f:
        content = f.read()
    bad = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
    good = "from torchvision.transforms.functional import rgb_to_grayscale"
    if bad in content:
        with open(target, "w") as f:
            f.write(content.replace(bad, good))
        print(f"  🔧 Patched basicsr → torchvision.transforms.functional")


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
# OpenVoice v2 checkpoints (S3 zip — not in the git repo)
# ---------------------------------------------------------------------------
print("\n=== OpenVoice v2 checkpoints ===")
OPENVOICE_V2_URL = (
    "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
)
ov2_zip = "/content/OpenVoice/checkpoints_v2.zip"
ov2_dir = "/content/OpenVoice/checkpoints_v2"
if os.path.exists(ov2_dir) and os.path.exists(
    os.path.join(ov2_dir, "converter", "checkpoint.pth")
):
    print(f"  ✓  Already exists: {ov2_dir}")
else:
    download_if_missing(OPENVOICE_V2_URL, ov2_zip)
    print("  📦 Extracting OpenVoice v2 weights…")
    with zipfile.ZipFile(ov2_zip, "r") as z:
        z.extractall("/content/OpenVoice/")
    print("  ✓  OpenVoice v2 weights ready.")

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

print("=== Applying compatibility patches ===")
_patch_basicsr()
print("=== Patches applied. ===\n")
