"""
AI Instagram Bot - Full Automation
Generates AI images + captions and posts to Instagram automatically.
"""

import os
import json
import time
import random
import requests
import base64
from datetime import datetime
from image_generator import generate_image
from caption_generator import generate_caption
from instagram_poster import post_to_instagram

# ── Load config ────────────────────────────────────────────────────────────────
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
GROQ_API_KEY           = os.environ["GROQ_API_KEY"]
HF_API_KEY             = os.environ["HF_API_KEY"]
IMGBB_API_KEY          = os.environ["IMGBB_API_KEY"]  # Free image hosting

# ── Content themes (rotated automatically) ─────────────────────────────────────
THEMES = [
    {"style": "fashion editorial", "setting": "luxury penthouse rooftop at golden hour", "vibe": "confident, glamorous"},
    {"style": "fitness aesthetic",  "setting": "modern gym with sunlight streaming in",  "vibe": "strong, energetic"},
    {"style": "beach lifestyle",    "setting": "tropical beach at sunset",               "vibe": "carefree, radiant"},
    {"style": "street fashion",     "setting": "Tokyo neon-lit streets at night",        "vibe": "edgy, cool"},
    {"style": "cozy aesthetic",     "setting": "minimalist café with warm lighting",     "vibe": "soft, approachable"},
    {"style": "glamour shot",       "setting": "professional studio with dramatic light","vibe": "fierce, powerful"},
    {"style": "travel influencer",  "setting": "Santorini white architecture at dawn",   "vibe": "dreamy, wanderlust"},
    {"style": "party ready",        "setting": "upscale rooftop lounge at night",        "vibe": "fun, magnetic"},
]

def get_todays_theme():
    """Rotate theme based on day of year so each day is different."""
    day_of_year = datetime.now().timetuple().tm_yday
    return THEMES[day_of_year % len(THEMES)]

def run_bot():
    print(f"🤖 Bot starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    theme = get_todays_theme()
    print(f"📸 Today's theme: {theme['style']} — {theme['setting']}")

    # 1. Generate image
    print("🎨 Generating AI image...")
    image_url = generate_image(theme, HF_API_KEY, IMGBB_API_KEY)
    if not image_url:
        print("❌ Image generation failed. Aborting.")
        return

    print(f"✅ Image ready: {image_url}")

    # 2. Generate caption + hashtags
    print("✍️  Generating caption...")
    caption = generate_caption(theme, GROQ_API_KEY)
    print(f"✅ Caption: {caption[:80]}...")

    # 3. Post to Instagram
    print("📤 Posting to Instagram...")
    result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)

    if result:
        print(f"🎉 Posted successfully! Post ID: {result}")
    else:
        print("❌ Posting failed.")

if __name__ == "__main__":
    run_bot()
