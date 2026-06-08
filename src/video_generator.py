"""
Video Generator — fal.ai image-to-video (Kling v1.6)
Animates the FLUX-generated image into a short hot Reel.
"""

import os
import requests
import fal_client

def generate_video(image_url: str, theme: dict, fal_api_key: str) -> bytes | None:
    os.environ["FAL_KEY"] = fal_api_key

    prompt = (
        f"beautiful young woman, {theme['style']}, {theme['setting']}, "
        f"{theme['vibe']}, subtle seductive movement, hair flowing, "
        "cinematic slow motion, hot, alluring, high quality"
    )

    print(f"  Submitting to fal.ai Kling v1.6...")
    try:
        result = fal_client.subscribe(
            "fal-ai/kling-video/v1.6/standard/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": "5",
                "aspect_ratio": "9:16",
            },
            with_logs=False,
        )

        video_url = result["video"]["url"]
        print(f"  Video generated: {video_url[:60]}...")

        response = requests.get(video_url, timeout=120)
        if response.status_code == 200:
            return response.content
        print(f"  Failed to download video: {response.status_code}")
        return None

    except Exception as e:
        print(f"  fal.ai error: {e}")
        return None
