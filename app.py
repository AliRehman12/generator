"""
AI Avatar Video Generator — Gradio 4.x app.

Tabs:
  1. Voice Setup      — clone a voice or use a Kokoro preset, preview audio
  2. Generate Avatar  — produce a talking-head video from photo + audio
  3. Body Animation   — full-body animation with MusePose (needs fresh session)
"""

import os
import shutil
import traceback
from datetime import datetime

import gradio as gr
import torch

from config import DEVICE, DRIVE_OUTPUT_DIR, TEMP_DIR
from modules.vram_utils import clear_vram, get_vram_usage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _system_status() -> str:
    lines = []
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        lines.append(f"GPU      : {props.name}")
        lines.append(f"VRAM     : {props.total_memory / 1e9:.1f} GB total")
        lines.append(f"CUDA     : {torch.version.cuda}")
    else:
        lines.append("GPU      : No CUDA GPU (running on CPU/MPS)")
    drive_ok = os.path.exists("/content/drive/MyDrive")
    lines.append(f"Drive    : {'Mounted ✓' if drive_ok else 'Not mounted — run Cell 1'}")
    return "\n".join(lines)


def _save_to_drive(src_path: str) -> str:
    if not src_path or not os.path.exists(src_path):
        return "No file to save."
    if not os.path.exists("/content/drive/MyDrive"):
        return "Google Drive is not mounted. Run Cell 1 in the notebook first."
    os.makedirs(DRIVE_OUTPUT_DIR, exist_ok=True)
    dst = os.path.join(DRIVE_OUTPUT_DIR, os.path.basename(src_path))
    shutil.copy2(src_path, dst)
    return f"Saved to Google Drive: {dst}"


# ---------------------------------------------------------------------------
# Tab 1 — Voice setup
# ---------------------------------------------------------------------------

def generate_audio_preview(
    reference_audio,
    script_text,
    language,
    speed,
    use_cloning,
    kokoro_voice,
    progress=gr.Progress(),
):
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, f"audio_preview_{_timestamp()}.wav")

        if use_cloning:
            if not reference_audio:
                return None, "Please upload or record a voice sample first."
            if not script_text or not script_text.strip():
                return None, "Please type the script you want the avatar to speak."

            progress(0.1, desc="Extracting speaker embedding…")
            from modules.voice_module import extract_speaker_embedding, clone_voice_to_audio

            embedding_path = extract_speaker_embedding(reference_audio)
            progress(0.5, desc="Synthesising speech in cloned voice…")
            clone_voice_to_audio(
                text=script_text,
                speaker_embedding_path=embedding_path,
                output_path=output_path,
                language=language,
                speed=float(speed),
            )
        else:
            if not script_text or not script_text.strip():
                return None, "Please type the script you want the avatar to speak."
            progress(0.3, desc="Generating speech with Kokoro TTS…")
            from modules.tts_module import generate_speech_kokoro

            generate_speech_kokoro(
                text=script_text,
                output_path=output_path,
                voice=kokoro_voice,
                speed=float(speed),
            )

        clear_vram()
        progress(1.0, desc="Done.")
        return output_path, f"Audio generated. VRAM: {get_vram_usage()}"

    except ValueError as e:
        return None, str(e)
    except FileNotFoundError as e:
        return None, str(e)
    except RuntimeError as e:
        err = str(e).lower()
        if "out of memory" in err:
            return None, (
                "GPU ran out of memory. Try switching to 256 resolution, or restart "
                "the Colab runtime and run the voice and avatar steps in separate sessions."
            )
        return None, f"Error: {e}"
    except Exception:
        return None, f"Unexpected error:\n{traceback.format_exc()}"


# ---------------------------------------------------------------------------
# Tab 2 — Generate avatar video
# ---------------------------------------------------------------------------

def generate_avatar_video(
    face_image,
    audio_file,
    expression_scale,
    preprocess,
    enhancer,
    size,
    still_mode,
    pose_style,
    progress=gr.Progress(),
):
    try:
        if not face_image:
            return None, "Please upload a face photo.", get_vram_usage()
        if not audio_file:
            return None, "Please generate or upload an audio file first.", get_vram_usage()

        os.makedirs(TEMP_DIR, exist_ok=True)
        output_dir = os.path.join(TEMP_DIR, f"avatar_{_timestamp()}")

        progress(0.05, desc=f"VRAM before load: {get_vram_usage()}")
        from modules.voice_module import unload_models as unload_voice
        unload_voice()

        progress(0.1, desc="Loading SadTalker…")
        from modules.talking_head import generate_talking_head, unload_models as unload_head

        enhancer_val = None if enhancer == "None" else enhancer

        progress(0.2, desc="Running face enhancement & animation…")
        video_path = generate_talking_head(
            source_image_path=face_image,
            audio_path=audio_file,
            output_dir=output_dir,
            still_mode=bool(still_mode),
            preprocess=preprocess,
            enhancer=enhancer_val,
            expression_scale=float(expression_scale),
            size=int(size),
            pose_style=int(pose_style),
        )

        progress(0.9, desc="Finalising video…")
        # Rename to timestamped filename in TEMP_DIR
        final_name = f"avatar_{_timestamp()}.mp4"
        final_path = os.path.join(TEMP_DIR, final_name)
        shutil.copy2(video_path, final_path)

        unload_head()
        clear_vram()
        progress(1.0, desc="Done.")
        return final_path, "Video generated successfully.", get_vram_usage()

    except FileNotFoundError as e:
        return None, str(e), get_vram_usage()
    except RuntimeError as e:
        err = str(e).lower()
        if "out of memory" in err:
            return None, (
                "GPU ran out of memory. Try switching to 256 resolution, or restart "
                "the Colab runtime and run the voice and avatar steps in separate sessions."
            ), get_vram_usage()
        if "no face" in err:
            return None, (
                "No face detected in your photo. Use a clear, frontal photo with "
                "good lighting and no heavy filters."
            ), get_vram_usage()
        if "timed out" in err:
            return None, (
                "Generation timed out after 10 minutes. "
                "Try a shorter audio clip or 256 resolution."
            ), get_vram_usage()
        return None, f"Error: {e}", get_vram_usage()
    except Exception:
        return None, f"Unexpected error:\n{traceback.format_exc()}", get_vram_usage()


def save_video_to_drive(video_path):
    return _save_to_drive(video_path)


# ---------------------------------------------------------------------------
# Tab 3 — Body animation
# ---------------------------------------------------------------------------

def animate_body_video(
    ref_image,
    driving_video,
    out_width,
    out_height,
    progress=gr.Progress(),
):
    try:
        if not ref_image:
            return None, "Please upload a full-body photo."
        if not driving_video:
            return None, "Please upload a reference motion video."

        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, f"body_{_timestamp()}.mp4")

        progress(0.1, desc="Loading MusePose…")
        from modules.body_module import animate_body

        progress(0.2, desc="Animating body — this may take several minutes…")
        result = animate_body(
            reference_image_path=ref_image,
            driving_video_path=driving_video,
            output_path=output_path,
            width=int(out_width),
            height=int(out_height),
        )

        progress(1.0, desc="Done.")
        return result, "Body animation complete."

    except FileNotFoundError as e:
        return None, str(e)
    except RuntimeError as e:
        err = str(e).lower()
        if "out of memory" in err or "12 gb" in err:
            return None, (
                "GPU ran out of memory. Try switching to 256 resolution, or restart "
                "the Colab runtime and run the voice and avatar steps in separate sessions."
            )
        if "timed out" in err:
            return None, (
                "Generation timed out after 10 minutes. "
                "Try a shorter audio clip or 256 resolution."
            )
        return None, f"Error: {e}"
    except Exception:
        return None, f"Unexpected error:\n{traceback.format_exc()}"


# ---------------------------------------------------------------------------
# Build Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="AI Avatar Video Generator", theme=gr.themes.Soft()) as demo:

    gr.Markdown(
        """
        # 🎭 AI Avatar Video Generator
        Upload a face photo and a voice sample — get a talking-head video in minutes.
        Powered by **SadTalker** + **OpenVoice v2** on Google Colab T4.
        """
    )

    # System status card (populated on load)
    system_info = gr.Textbox(
        label="System status",
        value=_system_status,
        interactive=False,
        lines=4,
    )

    # ------------------------------------------------------------------
    # Tab 1 — Voice Setup
    # ------------------------------------------------------------------
    with gr.Tab("🎙️ Voice Setup"):
        gr.Markdown("### Step 1 — Generate your audio")

        with gr.Row():
            with gr.Column():
                ref_audio = gr.Audio(
                    sources=["upload", "microphone"],
                    type="filepath",
                    label="Upload or record your voice sample (5–30 sec)",
                )
                script_box = gr.Textbox(
                    label="Script — type what you want the avatar to say",
                    lines=4,
                    placeholder="Hello! I'm your AI avatar. What would you like me to say today?",
                )
                with gr.Row():
                    lang_dd = gr.Dropdown(
                        choices=["EN", "ES", "FR", "ZH", "JP", "KR"],
                        value="EN",
                        label="Language",
                    )
                    speed_sl = gr.Slider(
                        0.7, 1.3, value=1.0, step=0.1, label="Speaking speed"
                    )
                use_cloning_cb = gr.Checkbox(
                    label="Use voice cloning (uncheck to use a preset Kokoro voice)",
                    value=True,
                )
                kokoro_dd = gr.Dropdown(
                    choices=["af_heart", "af_bella", "am_adam", "bf_emma", "bm_george"],
                    value="af_heart",
                    label="Kokoro preset voice (active when cloning is OFF)",
                    visible=False,
                )
                gen_audio_btn = gr.Button("🔊 Generate audio preview", variant="primary")

            with gr.Column():
                audio_preview = gr.Audio(label="Audio preview — listen before generating video")
                audio_status = gr.Textbox(label="Status", interactive=False, lines=3)

        # Show/hide Kokoro dropdown
        use_cloning_cb.change(
            fn=lambda v: gr.update(visible=not v),
            inputs=use_cloning_cb,
            outputs=kokoro_dd,
        )

        gen_audio_btn.click(
            fn=generate_audio_preview,
            inputs=[ref_audio, script_box, lang_dd, speed_sl, use_cloning_cb, kokoro_dd],
            outputs=[audio_preview, audio_status],
        )

    # ------------------------------------------------------------------
    # Tab 2 — Generate Avatar Video
    # ------------------------------------------------------------------
    with gr.Tab("🎬 Generate Avatar Video"):
        gr.Markdown("### Step 2 — Create your talking-head video")
        gr.Markdown(
            "> **Photo tips:** Use a clear frontal face shot, good lighting, "
            "no sunglasses, plain background preferred."
        )

        with gr.Row():
            with gr.Column():
                face_img = gr.Image(
                    type="filepath",
                    label="Upload your face photo (frontal, well-lit)",
                )
                avatar_audio = gr.Audio(
                    type="filepath",
                    label="Audio file (auto-filled from Tab 1 — or upload separately)",
                )

                with gr.Accordion("⚙️ Advanced settings", open=False):
                    expr_sl = gr.Slider(
                        0.5, 2.0, value=1.0, step=0.1, label="Expression intensity"
                    )
                    preprocess_dd = gr.Dropdown(
                        choices=["crop", "full", "extcrop"],
                        value="crop",
                        label="Face preprocess mode",
                    )
                    enhancer_dd = gr.Dropdown(
                        choices=["gfpgan", "RestoreFormer", "None"],
                        value="gfpgan",
                        label="Face enhancer",
                    )
                    size_dd = gr.Dropdown(
                        choices=[256, 512],
                        value=256,
                        label="Resolution (512 uses more VRAM)",
                    )
                    still_cb = gr.Checkbox(
                        label="Still mode (less head movement)", value=False
                    )
                    pose_sl = gr.Slider(
                        0, 45, value=0, step=1, label="Pose style (0 = natural)"
                    )

                vram_status = gr.Textbox(
                    label="GPU VRAM status",
                    value=get_vram_usage,
                    interactive=False,
                )
                gen_video_btn = gr.Button(
                    "🎭 Generate talking avatar video", variant="primary"
                )

            with gr.Column():
                avatar_video = gr.Video(label="Your talking avatar")
                video_status = gr.Textbox(label="Status", interactive=False, lines=3)
                save_btn = gr.Button("💾 Save to Google Drive")
                save_status = gr.Textbox(label="Drive save status", interactive=False)

        # Auto-fill audio from Tab 1
        audio_preview.change(
            fn=lambda x: x,
            inputs=audio_preview,
            outputs=avatar_audio,
        )

        gen_video_btn.click(
            fn=generate_avatar_video,
            inputs=[
                face_img, avatar_audio, expr_sl, preprocess_dd,
                enhancer_dd, size_dd, still_cb, pose_sl,
            ],
            outputs=[avatar_video, video_status, vram_status],
        )

        save_btn.click(
            fn=save_video_to_drive,
            inputs=avatar_video,
            outputs=save_status,
        )

    # ------------------------------------------------------------------
    # Tab 3 — Body Animation
    # ------------------------------------------------------------------
    with gr.Tab("🕺 Body Animation (optional)"):
        gr.Markdown(
            """
            ### Step 3 — Full-body animation with MusePose

            > ⚠️ **Body animation requires ~12 GB VRAM.**
            > Make sure you have **NOT** loaded voice/avatar models in the same session,
            > or **restart the runtime** before running this tab.
            """
        )

        with gr.Row():
            with gr.Column():
                body_img = gr.Image(
                    type="filepath",
                    label="Full or half-body photo",
                )
                driving_vid = gr.Video(
                    label="Reference motion video (gesture / dance driving video)",
                )
                with gr.Row():
                    body_width = gr.Slider(
                        256, 768, value=512, step=64, label="Output width"
                    )
                    body_height = gr.Slider(
                        256, 1024, value=768, step=64, label="Output height"
                    )
                body_btn = gr.Button("🕺 Animate body", variant="primary")

            with gr.Column():
                body_video = gr.Video(label="Body animation output")
                body_status = gr.Textbox(label="Status", interactive=False, lines=3)

        body_btn.click(
            fn=animate_body_video,
            inputs=[body_img, driving_vid, body_width, body_height],
            outputs=[body_video, body_status],
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(share=True, debug=False)
