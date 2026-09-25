"""
Text-on-photo overlays — the punchy on-screen text real influencer
Reels/posts use ("Outfit of the Day", "This view though"), burned
directly into the image/video, separate from the Instagram caption
text below the post.
"""

import random
from PIL import Image, ImageDraw, ImageFont

OVERLAY_CHANCE = 0.85

OVERLAY_PHRASES = [
    "Outfit of the day",
    "This view though 😍",
    "POV: perfect beach day",
    "Rating this sunset: 10/10",
    "When the ocean hits different",
    "Golden hour magic ✨",
    "Beach mode: activated",
    "Main character energy",
    "Not asking for permission",
    "This is your sign to relax",
]

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Ubuntu (GH runner)
    "C:/Windows/Fonts/arialbd.ttf",  # local Windows testing
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


def decide_overlay_text() -> str | None:
    """Call once per post/video so a Reel's multiple shots all get the
    same overlay text instead of a different random phrase per frame."""
    if random.random() >= OVERLAY_CHANCE:
        return None
    return random.choice(OVERLAY_PHRASES)


def add_overlay_text(im: Image.Image, text: str) -> Image.Image:
    """Burn the given phrase onto the image, styled like real Reels text
    overlays: bold white text with a dark shadow.

    Positioned around 68% down the frame rather than near the top: our
    prompts request head-to-knees full-body framing, so the top ~25% is
    where the face/head actually sits (confirmed by a real test post -
    top-third text landed right across the face). The ~68-82% band sits
    below the torso/face and above where Instagram's own UI chrome
    (caption, like/comment icons) covers the bottom ~15% in the Reels
    player, so it clears both without needing real face detection."""
    im = im.convert("RGB")
    draw = ImageDraw.Draw(im)

    font_size = max(28, im.width // 14)
    font = _load_font(font_size)

    # Wrap long phrases to fit within ~85% of image width
    max_width = int(im.width * 0.85)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_height = int(font_size * 1.25)
    y = int(im.height * 0.68)

    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (im.width - line_width) / 2
        shadow_offset = max(2, font_size // 16)
        # Dark shadow for legibility against any background
        for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset),
                       (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    return im
