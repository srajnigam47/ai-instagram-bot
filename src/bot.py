"""
AI Instagram Bot — Full Automation
Posts AI-generated videos (Reels) with music to Instagram automatically.
"""

import os
import time
import tempfile
from datetime import datetime
from image_generator import generate_image
from video_generator import generate_video
from audio_mixer import mix_audio
from caption_generator import generate_caption
from instagram_poster import post_to_instagram, post_reel_to_instagram
from video_uploader import upload_video, delete_release

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
GROQ_API_KEY           = os.environ["GROQ_API_KEY"]
HF_API_KEY             = os.environ["HF_API_KEY"]
IMGBB_API_KEY          = os.environ["IMGBB_API_KEY"]

THEMES = [
    {"style": "fashion editorial",  "setting": "luxury penthouse rooftop at golden hour", "vibe": "confident, glamorous"},
    {"style": "fitness aesthetic",  "setting": "modern gym with sunlight streaming in",   "vibe": "strong, energetic"},
    {"style": "beach lifestyle",    "setting": "tropical beach at sunset",                "vibe": "carefree, radiant"},
    {"style": "street fashion",     "setting": "Tokyo neon-lit streets at night",         "vibe": "edgy, cool"},
    {"style": "cozy aesthetic",     "setting": "minimalist café with warm lighting",      "vibe": "soft, approachable"},
    {"style": "glamour shot",       "setting": "professional studio with dramatic light", "vibe": "fierce, powerful"},
    {"style": "travel influencer",  "setting": "Santorini white architecture at dawn",    "vibe": "dreamy, wanderlust"},
    {"style": "party ready",        "setting": "upscale rooftop lounge at night",         "vibe": "fun, magnetic"},
]

def get_todays_theme():
    day_of_year = datetime.now().timetuple().tm_yday
    return THEMES[day_of_year % len(THEMES)]

def post_image_fallback(image_url, caption):
    result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)
    if result:
        print(f"Image posted as fallback. Post ID: {result}")
    else:
        print("Image fallback also failed.")

def run_bot():
    print(f"Bot starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    theme = get_todays_theme()
    print(f"Theme: {theme['style']} — {theme['setting']}")

    # Step 1: Generate base image
    print("Generating AI image...")
    image_url = generate_image(theme, HF_API_KEY, IMGBB_API_KEY)
    if not image_url:
        print("Image generation failed. Aborting.")
        return
    print(f"Image ready: {image_url}")

    # Step 2: Generate caption
    print("Generating caption...")
    caption = generate_caption(theme, GROQ_API_KEY)
    print(f"Caption: {caption[:80]}...")

    # Step 3: Generate video + mix music
    print("Generating video...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_bytes = generate_video(image_url, theme, HF_API_KEY, tmp_dir)

        if not video_bytes:
            print("Video generation failed — posting image instead.")
            post_image_fallback(image_url, caption)
            return

        print(f"Video generated ({len(video_bytes)//1024}KB)")
        print("Mixing music...")
        final_video = mix_audio(video_bytes, tmp_dir)
        print(f"Final video: {len(final_video)//1024}KB")

        # Step 4: Upload to GitHub Releases
        print("Uploading video...")
        video_url, release_id = upload_video(final_video)

        if not video_url:
            print("Video upload failed — posting image instead.")
            post_image_fallback(image_url, caption)
            return

        # Step 5: Post as Reel
        print("Posting Reel to Instagram...")
        post_id = post_reel_to_instagram(
            video_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
        )

        if post_id:
            print(f"Reel posted! Post ID: {post_id}")
        else:
            print("Reel failed — posting image instead.")
            post_image_fallback(image_url, caption)

        # Step 6: Clean up GitHub Release
        time.sleep(30)
        delete_release(release_id)

if __name__ == "__main__":
    run_bot()
