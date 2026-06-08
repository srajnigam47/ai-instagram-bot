"""
AI Instagram Bot — Full Automation
Posts AI-generated videos (Reels) with music to Instagram automatically.
"""

import os
import tempfile
import random
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
FAL_API_KEY            = os.environ.get("FAL_API_KEY", "")  # optional

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

def run_bot():
    print(f"Bot starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    theme = get_todays_theme()
    print(f"Theme: {theme['style']} — {theme['setting']}")

    # Step 1: Generate image (base for video)
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

    # Step 3: Generate video from image
    print("Generating video...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_bytes = generate_video(image_url, theme, HF_API_KEY, tmp_dir)

        if video_bytes:
            print(f"Video generated ({len(video_bytes)//1024}KB)")

            # Step 4: Mix music into video
            print("Mixing music...")
            final_video = mix_audio(video_bytes, tmp_dir)
            print(f"Final video size: {len(final_video)//1024}KB")

        # Step 5: Upload to GitHub Releases for public URL
        print("Uploading video...")
        video_url, release_id = upload_video(final_video)

        if video_url:
            # Step 6: Post as Reel
            print("Posting Reel to Instagram...")
            post_id = post_reel_to_instagram(
                video_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
            )
            if post_id:
                print(f"Reel posted! Post ID: {post_id}")
            else:
                print("Reel posting failed.")

            # Step 7: Clean up GitHub Release
            import time
            time.sleep(30)  # Give Instagram time to download the video
            delete_release(release_id)
            else:
                print("Video upload failed — falling back to image post.")
                result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)
                if result:
                    print(f"Image posted as fallback. Post ID: {result}")
        else:
            print("Video generation failed — falling back to image post.")
            result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)
            if result:
                print(f"Image posted as fallback. Post ID: {result}")

if __name__ == "__main__":
    run_bot()
