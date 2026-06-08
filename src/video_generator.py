"""
Video Generator — 100% Free
Generates 3 FLUX images of the AI girl, then uses ffmpeg to create
a smooth video with Ken Burns zoom + transitions between shots.
No external video API needed.
"""

import os
import subprocess
import requests
import tempfile
import time

HF_BASE = "https://router.huggingface.co/hf-inference/models"

HF_MODELS = [
    ("black-forest-labs/FLUX.1-schnell", "flux"),
    ("black-forest-labs/FLUX.1-dev",     "flux"),
    ("stabilityai/stable-diffusion-2-1", "sd"),
]

def build_shot_prompt(theme: dict, shot: int) -> str:
    base = (
        "beautiful young woman, dark hair, hazel eyes, perfect skin, "
        "natural makeup, photorealistic, hyperdetailed face, "
    )
    shots = [
        f"{base}{theme['style']}, {theme['setting']}, {theme['vibe']} expression, "
        "full body shot, professional photography, 8k, cinematic, Instagram model",

        f"{base}{theme['style']}, {theme['setting']}, confident smile, "
        "close up face and shoulders, bokeh background, magazine quality, cinematic",

        f"{base}{theme['style']}, {theme['setting']}, {theme['vibe']}, "
        "mid shot, dramatic lighting, sharp focus, luxury aesthetic",
    ]
    return shots[shot % len(shots)]

def download_image(url: str, path: str) -> bool:
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"  Image download error: {e}")
    return False

def generate_hf_image(prompt: str, api_key: str) -> bytes | None:
    headers = {"Authorization": f"Bearer {api_key}"}
    for model, style in HF_MODELS:
        url = f"{HF_BASE}/{model}"
        payload = {"inputs": prompt} if style == "flux" else {
            "inputs": prompt,
            "parameters": {"num_inference_steps": 25, "guidance_scale": 7.5,
                           "width": 768, "height": 1344}
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                return r.content
            elif r.status_code == 503:
                time.sleep(20)
                r = requests.post(url, headers=headers, json=payload, timeout=120)
                if r.status_code == 200:
                    return r.content
            else:
                print(f"  HF {model}: {r.status_code}")
        except Exception as e:
            print(f"  HF error: {e}")
    return None

def images_to_video(image_paths: list[str], tmp_dir: str, duration_each: int = 3) -> bytes | None:
    """
    Use ffmpeg to create a smooth vertical video from multiple images.
    Each image gets a Ken Burns zoom effect + crossfade transition.
    """
    if not image_paths:
        return None

    output_path = os.path.join(tmp_dir, "slideshow.mp4")
    n = len(image_paths)

    # Build ffmpeg filter for ken burns + crossfade transitions
    filter_parts = []
    inputs = []
    for i, img_path in enumerate(image_paths):
        inputs += ["-loop", "1", "-t", str(duration_each + 1), "-i", img_path]
        zoom_dir = "in" if i % 2 == 0 else "out"
        if zoom_dir == "in":
            zoom_expr = "min(zoom+0.0008,1.4)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr = "max(zoom-0.0008,1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        fps = 25
        d = duration_each * fps
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={d}:s=1080x1920:fps={fps},"
            f"setpts=PTS-STARTPTS,fps={fps}[v{i}]"
        )

    # Crossfade between clips
    if n == 1:
        concat_filter = "[v0]"
    else:
        xfade_parts = []
        prev = "[v0]"
        offset = duration_each - 1
        for i in range(1, n):
            out = f"[xf{i}]" if i < n - 1 else "[vout]"
            xfade_parts.append(f"{prev}[v{i}]xfade=transition=fade:duration=1:offset={offset}{out}")
            prev = f"[xf{i}]"
            offset += duration_each - 1
        concat_filter = ";".join(xfade_parts)

    if n == 1:
        final_filter = ";".join(filter_parts) + f";[v0]copy[vout]"
    else:
        final_filter = ";".join(filter_parts) + ";" + concat_filter

    cmd = [
        "ffmpeg", "-y",
    ] + inputs + [
        "-filter_complex", final_filter,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        return None

    with open(output_path, "rb") as f:
        return f.read()

def generate_video(image_url: str, theme: dict, hf_api_key: str, tmp_dir: str = None) -> bytes | None:
    """
    Generate 3 AI girl images and stitch into a smooth Reel video.
    image_url: the first image already generated (reuse it)
    """
    manage_tmp = tmp_dir is None
    if manage_tmp:
        import tempfile
        tmp_obj = tempfile.TemporaryDirectory()
        tmp_dir = tmp_obj.name

    image_paths = []

    # Reuse the already-generated first image
    img0_path = os.path.join(tmp_dir, "shot0.jpg")
    if download_image(image_url, img0_path):
        image_paths.append(img0_path)
        print(f"  Shot 1 ready (reused from image post)")

    # Generate 2 more shots
    for shot in range(1, 3):
        print(f"  Generating shot {shot + 1}...")
        prompt = build_shot_prompt(theme, shot)
        img_bytes = generate_hf_image(prompt, hf_api_key)
        if img_bytes:
            img_path = os.path.join(tmp_dir, f"shot{shot}.jpg")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            image_paths.append(img_path)
            print(f"  Shot {shot + 1} ready")
        else:
            print(f"  Shot {shot + 1} failed, skipping")

    if not image_paths:
        print("  No images generated for video")
        return None

    print(f"  Creating video from {len(image_paths)} shots...")
    video_bytes = images_to_video(image_paths, tmp_dir)

    if manage_tmp:
        tmp_obj.cleanup()

    return video_bytes
