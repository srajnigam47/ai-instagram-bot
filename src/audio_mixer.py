"""
Audio Mixer — picks from bundled royalty-free tracks; falls back to
ffmpeg synthetic beat if something's wrong with the local files.

Tracks in src/music/ are by Kevin MacLeod (incompetech.com), licensed
CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/) - free to use
including commercially, but requires attribution. Bundled locally
instead of downloaded at runtime because relying on incompetech.com
from GitHub Actions' shared IP ranges was unreliable (~2 of 5 tracks
succeeding per run; incompetech.com occasionally rate-limits/blocks
those IPs, and the archive.org backup URLs were permanently dead).
"""

import subprocess
import random
import os
import glob

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")

MUSIC_ATTRIBUTION = "Music: Kevin MacLeod (incompetech.com) — CC BY 3.0"


def pick_music(tmp_dir: str) -> str | None:
    tracks = glob.glob(os.path.join(MUSIC_DIR, "*.mp3"))
    if not tracks:
        print(f"  No bundled tracks found in {MUSIC_DIR}")
        return None
    track = random.choice(tracks)
    print(f"  Using bundled track: {os.path.basename(track)}")
    return track


def generate_synthetic_beat(tmp_dir: str, duration: int = 12) -> str | None:
    """Generate a simple electronic beat entirely with ffmpeg — no downloads."""
    path = os.path.join(tmp_dir, "beat.mp3")
    # 120 BPM kick on every beat + ambient A-minor chord pad
    expr = (
        "0.55*sin(2*PI*70*t)*exp(-mod(t*2,1)*10)"   # kick drum (120 BPM)
        "+0.12*sin(2*PI*220*t)"                       # A3 pad
        "+0.09*sin(2*PI*330*t)"                       # E4
        "+0.06*sin(2*PI*277*t)"                       # C#4
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc={expr}:s=44100:d={duration}",
        "-c:a", "libmp3lame", "-b:a", "128k",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("  Synthetic beat generated")
        return path
    print(f"  Synthetic beat failed: {result.stderr[-200:]}")
    return None


def mix_audio(video_bytes: bytes, tmp_dir: str) -> bytes:
    video_in  = os.path.join(tmp_dir, "raw.mp4")
    video_out = os.path.join(tmp_dir, "final.mp4")

    with open(video_in, "wb") as f:
        f.write(video_bytes)

    music_path = pick_music(tmp_dir) or generate_synthetic_beat(tmp_dir)

    if music_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_in,
            "-i", music_path,
            "-c:v", "copy",           # video is already correctly encoded — no re-encode
            "-c:a", "aac", "-b:a", "128k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            "-movflags", "+faststart",
            video_out,
        ]
    else:
        print("  No music available — posting silent video")
        cmd = [
            "ffmpeg", "-y",
            "-i", video_in,
            "-c:v", "copy", "-an",
            "-movflags", "+faststart",
            video_out,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Audio mix failed: {result.stderr[-300:]}")
        return video_bytes  # return original on failure

    with open(video_out, "rb") as f:
        return f.read()
