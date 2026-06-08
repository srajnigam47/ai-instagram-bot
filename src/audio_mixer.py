"""
Audio Mixer — downloads royalty-free music and mixes it with the video using ffmpeg.
All tracks are CC0/royalty-free from Internet Archive and Free Music Archive.
"""

import subprocess
import requests
import random
import tempfile
import os

# Royalty-free hot/electronic/pop tracks — stable direct download URLs
MUSIC_TRACKS = [
    "https://archive.org/download/bass-house-loop/bass-house-loop.mp3",
    "https://archive.org/download/lofi-chill-beats/lofi-chill-beats.mp3",
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Broke_For_Free/Directionless_EP/Broke_For_Free_-_01_-_Night_Owl.mp3",
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/WFMU/Jahzzar/Tumbling_Dishes_Like_Old-Mans_Wishes/Jahzzar_-_05_-_Siesta.mp3",
    "https://archive.org/download/Kevin_MacLeod_-_Funkorama/Funkorama.mp3",
    "https://archive.org/download/Kevin_MacLeod_-_Rollin_at_5/Rollin_at_5.mp3",
    "https://archive.org/download/incompetech-floatinpoint/FloatinPoint.mp3",
]

def download_music(tmp_dir: str) -> str | None:
    """Try each music URL until one downloads successfully."""
    tracks = MUSIC_TRACKS.copy()
    random.shuffle(tracks)

    for url in tracks:
        try:
            print(f"  Downloading music: {url.split('/')[-1]}")
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 10000:
                music_path = os.path.join(tmp_dir, "music.mp3")
                with open(music_path, "wb") as f:
                    f.write(r.content)
                print(f"  Music downloaded ({len(r.content)//1024}KB)")
                return music_path
        except Exception as e:
            print(f"  Music URL failed: {e}")
            continue

    print("  All music URLs failed — using silent audio")
    return None

def mix_audio(video_bytes: bytes, tmp_dir: str) -> bytes:
    """Mix royalty-free music into the video using ffmpeg."""
    video_in  = os.path.join(tmp_dir, "input.mp4")
    video_out = os.path.join(tmp_dir, "output.mp4")

    with open(video_in, "wb") as f:
        f.write(video_bytes)

    music_path = download_music(tmp_dir)

    if music_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_in,
            "-i", music_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-movflags", "+faststart",
            video_out
        ]
    else:
        # No music — just re-encode to correct format
        cmd = [
            "ffmpeg", "-y",
            "-i", video_in,
            "-c:v", "libx264",
            "-an",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-movflags", "+faststart",
            video_out
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-300:]}")
        return video_bytes  # return original if ffmpeg fails

    with open(video_out, "rb") as f:
        return f.read()
