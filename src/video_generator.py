"""
Video Generator — FREE
3 FLUX portrait shots → ffmpeg Ken Burns zoom + crossfade → 9:16 MP4
"""

import os
import subprocess
import requests
from image_generator import generate_hf_image, build_shot_prompt, process_image


def images_to_video(image_paths: list, tmp_dir: str, duration_each: int = 4) -> bytes | None:
    if not image_paths:
        return None

    output_path = os.path.join(tmp_dir, "slideshow.mp4")
    n = len(image_paths)
    fps = 25

    inputs = []
    filter_parts = []

    for i, img in enumerate(image_paths):
        # A single input frame: zoompan below generates exactly `d` output
        # frames from it. Without this, "-loop 1 -t N" defaults to ~25fps,
        # feeding zoompan dozens of duplicate frames — and it emits `d`
        # frames for EACH one it receives, blowing the video up ~100x
        # (measured: a 12s clip came out 506s long and never finished
        # encoding within any reasonable timeout).
        inputs += ["-loop", "1", "-framerate", "1", "-t", "0.5", "-i", img]
        d = duration_each * fps
        # Alternate zoom direction for cinematic variety
        if i % 2 == 0:
            z = "min(zoom+0.0006,1.3)"
        else:
            z = "max(zoom-0.0006,1.0)"
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps},"
            f"setpts=PTS-STARTPTS,fps={fps}[v{i}]"
        )

    if n == 1:
        final_filter = ";".join(filter_parts) + ";[v0]copy[vout]"
    else:
        xfades = []
        prev   = "[v0]"
        offset = duration_each - 1
        for i in range(1, n):
            out = f"[xf{i}]" if i < n - 1 else "[vout]"
            xfades.append(
                f"{prev}[v{i}]xfade=transition=fade:duration=1:offset={offset}{out}"
            )
            prev    = f"[xf{i}]"
            offset += duration_each - 1
        final_filter = ";".join(filter_parts) + ";" + ";".join(xfades)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", final_filter,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-movflags", "+faststart",
            output_path,
        ]
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print("  ffmpeg timed out")
        return None

    if result.returncode != 0:
        print(f"  ffmpeg error:\n{result.stderr[-1000:]}")
        return None

    with open(output_path, "rb") as f:
        return f.read()


def generate_video(
    image_url: str, theme: dict, hf_api_key: str, tmp_dir: str, seed: int = 0
) -> bytes | None:
    image_paths = []

    # Reuse the already-generated shot 0 (no extra API call)
    shot0 = os.path.join(tmp_dir, "shot0.jpg")
    try:
        r = requests.get(image_url, timeout=30)
        if r.status_code == 200:
            with open(shot0, "wb") as f:
                f.write(r.content)
            image_paths.append(shot0)
            print("  Shot 1 ready (reused)")
    except Exception as e:
        print(f"  Shot 0 download failed: {e}")

    # Generate 2 more portrait shots with different angles
    for shot in range(1, 3):
        print(f"  Generating shot {shot + 1}...")
        prompt    = build_shot_prompt(theme, shot, seed)
        img_bytes = generate_hf_image(prompt, hf_api_key)
        if img_bytes:
            img_bytes = process_image(img_bytes)
            p = os.path.join(tmp_dir, f"shot{shot}.jpg")
            with open(p, "wb") as f:
                f.write(img_bytes)
            image_paths.append(p)
            print(f"  Shot {shot + 1} ready")
        else:
            print(f"  Shot {shot + 1} failed, skipping")

    if not image_paths:
        return None

    print(f"  Stitching {len(image_paths)} shots...")
    return images_to_video(image_paths, tmp_dir)
