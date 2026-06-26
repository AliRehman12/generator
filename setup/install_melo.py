"""
Install MeloTTS for OpenVoice voice cloning.

MeloTTS does not reliably install on Python 3.12 (Colab default).
On 3.12 we try a no-deps editable install; if that fails, use runtime 2025.07.
"""

import os
import subprocess
import sys


MELO_DIR = "/content/MeloTTS"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def install_melo() -> bool:
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"Python {major}.{minor}")

    if (major, minor) >= (3, 12):
        print(
            "⚠️  Python 3.12 detected — MeloTTS often fails here.\n"
            "   Recommended: Runtime → Change runtime type → Runtime version → 2025.07\n"
            "   Then Runtime → Restart session and re-run setup."
        )

    run(["pip", "install", "-q", "--upgrade", "pip", "setuptools", "wheel"])

    run(
        [
            "pip",
            "install",
            "-q",
            "cn2an",
            "pypinyin",
            "inflect",
            "unidecode",
            "eng-to-ipa",
            "pydub",
            "nltk",
            "loguru",
            "tqdm",
            "cached_path",
            "gruut-ipa",
            "gruut_lang_en",
            "gruut_lang_de",
            "gruut_lang_es",
            "gruut_lang_fr",
        ]
    )

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

    # gruut core often fails to build on 3.12 — English may still work without it
    gruut = subprocess.run(["pip", "install", "-q", "gruut==2.2.3"], capture_output=True)
    if gruut.returncode != 0:
        print("  gruut core skipped (English-only voice cloning may still work)")

    if (major, minor) < (3, 12):
        # Python 3.11 and below: standard install usually works
        try:
            run(["pip", "install", "-q", "git+https://github.com/myshell-ai/MeloTTS.git"])
        except subprocess.CalledProcessError:
            run(["pip", "install", "-q", "--no-deps", "-e", MELO_DIR])
    else:
        run(["pip", "install", "-q", "--no-deps", "-e", MELO_DIR])

    run(
        [
            sys.executable,
            "-c",
            "import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True)",
        ]
    )

    try:
        from melo.api import TTS  # noqa: F401

        print("✅ MeloTTS installed successfully")
        return True
    except Exception as exc:
        print(f"❌ MeloTTS import failed: {exc}")
        print(
            "\nVoice cloning will NOT work until MeloTTS is installed.\n"
            "You can still use Kokoro preset voices (uncheck 'Use voice cloning' in the app).\n\n"
            "Fix for Colab:\n"
            "  1. Runtime → Change runtime type\n"
            "  2. Hardware accelerator: GPU (T4)\n"
            "  3. Runtime version: 2025.07  ← Python 3.11\n"
            "  4. Save → Restart session → re-run setup cells"
        )
        return False


if __name__ == "__main__":
    sys.exit(0 if install_melo() else 1)
