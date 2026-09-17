"""
AI Instagram Bot — Full Automation
Posts AI-generated Reels with music to Instagram 3x/day.
"""

import os
import sys
import time
import tempfile
from datetime import datetime, timedelta, timezone

from image_generator   import generate_image
from video_generator   import generate_video
from audio_mixer       import mix_audio
from caption_generator import generate_caption
from instagram_poster  import post_to_instagram, post_reel_to_instagram
from video_uploader    import upload_video, delete_release
from post_state        import get_last_post_time, set_last_post_time

INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_ACCOUNT_ID   = os.environ["INSTAGRAM_ACCOUNT_ID"]
GROQ_API_KEY           = os.environ["GROQ_API_KEY"]
HF_API_KEY             = os.environ["HF_API_KEY"]
IMGBB_API_KEY          = os.environ["IMGBB_API_KEY"]

# Target ~5 posts/day. The workflow runs every 30 min as a cheap check-in
# (GitHub's own cron trigger is known to silently skip firings on
# low-traffic repos) rather than 5 exact-time slots that all must fire.
MIN_POST_INTERVAL = timedelta(hours=4, minutes=30)

THEMES = [
    {"style": "beach lifestyle",      "setting": "tropical beach at sunset, turquoise water",   "vibe": "carefree, radiant"},
    {"style": "poolside glam",        "setting": "resort infinity pool at golden hour",         "vibe": "relaxed, glowing"},
    {"style": "bikini beach day",     "setting": "white sand beach, clear blue water, midday",  "vibe": "playful, sun-kissed"},
    {"style": "tropical golden hour", "setting": "palm-lined beach at sunset, warm light",       "vibe": "dreamy, warm"},
    {"style": "fitness aesthetic",    "setting": "beachfront boardwalk at sunrise",              "vibe": "strong, energetic"},
    {"style": "resort vacation",      "setting": "luxury beach resort balcony, ocean view",      "vibe": "breezy, elegant"},
    {"style": "glamour swimwear",     "setting": "poolside cabana with dramatic light",          "vibe": "fierce, confident"},
    {"style": "sunset beach party",   "setting": "beach bonfire gathering at dusk",              "vibe": "fun, magnetic"},
]

def _seed() -> int:
    now = datetime.now()
    # Unique per day × posting slot so each run gets different prompts
    return now.timetuple().tm_yday * 10 + (now.hour // 5)

def _post_image(image_url: str, caption: str) -> bool:
    result = post_to_instagram(image_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID)
    print(f"  Image post ID: {result}" if result else "  Image post also failed.")
    return bool(result)

def run_bot():
    print(f"Bot starting — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    is_manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    if not is_manual:
        last_post = get_last_post_time()
        if last_post is not None:
            elapsed = datetime.now(timezone.utc) - last_post
            if elapsed < MIN_POST_INTERVAL:
                remaining = MIN_POST_INTERVAL - elapsed
                print(f"  Last post was {elapsed} ago (< {MIN_POST_INTERVAL}); "
                      f"skipping this check-in, next post in ~{remaining}.")
                return

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
        sys.exit(1)
    print(f"  {image_url}")

    # 3. Video + music
    print("\n[3/5] Building video...")
    with tempfile.TemporaryDirectory() as tmp:
        video = generate_video(image_url, theme, HF_API_KEY, tmp, seed)

        if not video:
            print("  Video failed — posting image instead.")
            if not _post_image(image_url, caption):
                sys.exit(1)
            set_last_post_time()
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
            if not _post_image(image_url, caption):
                sys.exit(1)
            set_last_post_time()
            return

        post_id = post_reel_to_instagram(
            video_url, caption, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
        )

        if post_id:
            print(f"\nReel posted! ID: {post_id}")
            set_last_post_time()
        else:
            print("  Reel failed — posting image instead.")
            if not _post_image(image_url, caption):
                sys.exit(1)
            set_last_post_time()

        # Clean up the temporary GitHub Release
        time.sleep(30)
        delete_release(release_id)

if __name__ == "__main__":
    run_bot()
