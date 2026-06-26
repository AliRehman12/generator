"""
Install MeloTTS for OpenVoice voice cloning.

Requires Python 3.11 (Colab runtime version 2025.07).
Python 3.12 is not supported by MeloTTS upstream.
"""

import os
import subprocess
import sys

MELO_DIR = "/content/MeloTTS"

# English voice-cloning deps (from MeloTTS setup.py)
MELO_EN_DEPS = [
    "anyascii==0.3.2",
    "g2p_en==2.1.0",
    "txtsplit",
    "jamo==0.4.1",
    "langid==1.1.6",
    "num2words==0.5.12",
    "cn2an==0.5.22",
    "inflect==7.0.0",
    "pypinyin==0.50.0",
    "unidecode==1.3.7",
    "loguru==0.7.2",
    "tensorboard==2.16.2",
    "eng-to-ipa",
    "pydub",
    "nltk",
    "tqdm",
    "cached_path",
    "gruut-ipa",
    "gruut_lang_en",
    "mecab-python3",
    "unidic",
    "unidic-lite",
]


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def _ensure_melo_on_path():
    if os.path.isdir(MELO_DIR) and MELO_DIR not in sys.path:
        sys.path.insert(0, MELO_DIR)


def verify_melo() -> bool:
    _ensure_melo_on_path()
    try:
        from melo.api import TTS  # noqa: F401
        return True
    except Exception:
        return False


def install_melo() -> bool:
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"Python {major}.{minor}.{sys.version_info.micro}")

    if (major, minor) >= (3, 12):
        print(
            "\n❌ STOP: Python 3.12 — MeloTTS cannot be installed.\n"
            "   Voice cloning is disabled until you switch runtime.\n\n"
            "   Fix (required for voice cloning):\n"
            "     Runtime → Change runtime type\n"
            "     → Hardware accelerator: GPU (T4)\n"
            "     → Runtime version: 2025.07\n"
            "     → Save → Restart session → re-run setup\n"
        )
        return False

    # MeCab system libs + Japanese dictionary (MeloTTS imports japanese at load time)
    subprocess.run(
        ["apt-get", "install", "-y", "mecab", "libmecab-dev", "mecab-ipadic-utf8"],
        capture_output=True,
    )

    # setuptools 82+ breaks torch on Colab
    run(["pip", "install", "-q", "pip", "setuptools<82", "wheel"])

    run(["pip", "install", "-q"] + MELO_EN_DEPS)

    if not os.path.isdir(MELO_DIR):
        run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "https://github.com/myshell-ai/MeloTTS.git",
                MELO_DIR,
            ]
        )

    subprocess.run(["pip", "install", "-q", "gruut==2.2.3"], capture_output=True)

    try:
        run(["pip", "install", "-q", "git+https://github.com/myshell-ai/MeloTTS.git"])
    except subprocess.CalledProcessError:
        run(["pip", "install", "-q", "-e", MELO_DIR])

    run(
        [
            sys.executable,
            "-c",
            "import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True)",
        ]
    )

    print("  Downloading unidic dictionary (~500 MB, one-time)…")
    run([sys.executable, "-m", "unidic", "download"])

    if verify_melo():
        print("✅ MeloTTS installed successfully")
        return True

    print("❌ MeloTTS import failed after install.")
    print("   Run manually: python -m unidic download")
    print("   Then: Runtime version → 2025.07, restart, re-run setup.")
    return False


if __name__ == "__main__":
    sys.exit(0 if install_melo() else 1)
