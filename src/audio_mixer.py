"""
Audio Mixer — downloads royalty-free music; falls back to ffmpeg synthetic beat.
"""

import subprocess
import requests
import random
import os

# Royalty-free tracks (CC0 / public domain)
MUSIC_URLS = [
    # Kevin MacLeod — incompetech.com direct CDN
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Funkorama.mp3",
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Electro%20Sketch.mp3",
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Hyperfun.mp3",
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Blippy%20Trance.mp3",
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sneaky%20Snitch.mp3",
    # Archive.org backups
    "https://archive.org/download/Kevin_MacLeod_-_Funkorama/Funkorama.mp3",
    "https://archive.org/download/Kevin_MacLeod_-_Rollin_at_5/Rollin_at_5.mp3",
]


def download_music(tmp_dir: str) -> str | None:
    urls = MUSIC_URLS.copy()
    random.shuffle(urls)
    for url in urls:
        try:
            print(f"  Downloading: {url.split('/')[-1]}")
            r = requests.get(
                url, timeout=25,
                headers={"User-Agent": "Mozilla/5.0 (compatible; bot)"},
                allow_redirects=True,
            )
            if r.status_code == 200 and len(r.content) > 20_000:
                p = os.path.join(tmp_dir, "music.mp3")
                with open(p, "wb") as f:
                    f.write(r.content)
                print(f"  Music OK ({len(r.content) // 1024}KB)")
                return p
            print(f"  {url.split('/')[-1]}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  Download failed: {e}")
    return None


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

    music_path = download_music(tmp_dir) or generate_synthetic_beat(tmp_dir)

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
