"""
AI Instagram Bot — Full Automation
Posts AI-generated Reels with music to Instagram 3x/day.
"""

import os
import time
import tempfile
from datetime import datetime

from image_generator   import generate_image
from video_generator   import generate_video
from audio_mixer       import mix_audio
from caption_generator import generate_caption
from instagram_poster  import post_to_instagram, post_reel_to_instagram
from video_uploader    import upload_video, delete_release

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
GROQ_API_KEY           = os.environ["GROQ_API_KEY"]
HF_API_KEY             = os.environ["HF_API_KEY"]
IMGBB_API_KEY          = os.environ["IMGBB_API_KEY"]

THEMES = [
    {"style": "fashion editorial",  "setting": "luxury penthouse rooftop at golden hour",  "vibe": "confident, glamorous"},
    {"style": "fitness aesthetic",  "setting": "modern gym with sunlight streaming in",    "vibe": "strong, energetic"},
    {"style": "beach lifestyle",    "setting": "tropical beach at sunset",                 "vibe": "carefree, radiant"},
    {"style": "street fashion",     "setting": "Tokyo neon-lit streets at night",          "vibe": "edgy, cool"},
    {"style": "cozy aesthetic",     "setting": "minimalist café with warm lighting",       "vibe": "soft, approachable"},
    {"style": "glamour shot",       "setting": "professional studio with dramatic light",  "vibe": "fierce, powerful"},
    {"style": "travel influencer",  "setting": "Santorini white architecture at dawn",     "vibe": "dreamy, wanderlust"},
    {"style": "party ready",        "setting": "upscale rooftop lounge at night",          "vibe": "fun, magnetic"},
]

def _seed() -> int:
    now = datetime.now()
    # Unique per day × posting slot so each run gets different prompts
    return now.timetuple().tm_yday * 10 + (now.hour // 5)

def _post_image(image_url: str, caption: str):
    result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)
    print(f"  Image post ID: {result}" if result else "  Image post also failed.")

def run_bot():
    print(f"Bot starting — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    seed  = _seed()
    theme = THEMES[seed % len(THEMES)]
    print(f"Theme: {theme['style']} — {theme['setting']} (seed {seed})")

    # 1. Caption (fast, do first so failures don't waste image credits)
    print("\n[1/5] Generating caption...")
    caption = generate_caption(theme, GROQ_API_KEY)
    print(f"  {caption[:80]}...")

    # 2. Base image
    print("\n[2/5] Generating image...")
    image_url = generate_image(theme, HF_API_KEY, IMGBB_API_KEY, seed)
    if not image_url:
        print("  Image generation failed. Aborting.")
        return
    print(f"  {image_url}")

    # 3. Video + music
    print("\n[3/5] Building video...")
    with tempfile.TemporaryDirectory() as tmp:
        video = generate_video(image_url, theme, HF_API_KEY, tmp, seed)

        if not video:
            print("  Video failed — posting image instead.")
            _post_image(image_url, caption)
            return

        print(f"  Video: {len(video) // 1024}KB")
        print("\n[4/5] Mixing music...")
        final = mix_audio(video, tmp)
        print(f"  Final: {len(final) // 1024}KB")

        # 4. Upload to GitHub Releases as temporary public host
        print("\n[5/5] Uploading & posting Reel...")
        video_url, release_id = upload_video(final)

        if not video_url:
            print("  Upload failed — posting image instead.")
            _post_image(image_url, caption)
            return

        post_id = post_reel_to_instagram(
            video_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
        )

        if post_id:
            print(f"\nReel posted! ID: {post_id}")
        else:
            print("  Reel failed — posting image instead.")
            _post_image(image_url, caption)

        # Clean up the temporary GitHub Release
        time.sleep(30)
        delete_release(release_id)

if __name__ == "__main__":
    run_bot()
