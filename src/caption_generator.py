"""
Caption Generator — Groq API (FREE)
"""

import requests
import random

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

CAPTION_TONES = [
    "mysterious and magnetic",
    "confident and unapologetic",
    "dreamy and poetic",
    "playful and teasing",
    "fierce and empowering",
    "effortlessly cool",
    "soft and sensual",
]

# Normal influencer hashtags — NO AI keywords (those suppress reach)
HASHTAG_SETS = [
    "#beachvibes #bikinibody #beachday #summertime #oceanvibes #tanlines #beachlife #sunkissed #gorgeous #stunning",
    "#poolday #swimwear #resortwear #vacationmode #tropicalvibes #golden #glow #luxurylife #travelgram #wanderlust",
    "#beachbabe #islandlife #sunsetvibes #paradisefound #saltlife #bikini #beachbum #summerbody #instadaily #photooftheday",
    "#fitness #beachfit #glow #confidence #motivation #boss #queen #selflove #bodygoals #strongnotskinny",
    "#bonfire #beachparty #sunsetlovers #goldenhour #nightvibes #magic #lit #glam #vacay #summernights",
]

_SYSTEM = (
    "You are a copywriter for a top Instagram influencer. "
    "Write captions that stop the scroll: short, punchy, unforgettable. "
    "Write as a confident real woman — never mention AI. "
    "End with a question or CTA. Under 150 characters. "
    "Return ONLY the caption text, nothing else, no quotes."
)

# Occasionally use a longer, narrative "story" caption instead of the usual
# short punchy line — flirty and playful, ends with a comment-bait question.
# Stays SFW/suggestive-at-most, same boundary as everything else here.
STORY_CHANCE = 0.2
_STORY_SYSTEM = (
    "You are a copywriter for a top Instagram influencer. "
    "Write a short 2-4 sentence story/scenario caption — a tiny flirty "
    "moment from her day. Playful, teasing, confident tone. Write as a "
    "confident real woman — never mention AI. "
    "End with a fun, flirty question that invites comments. "
    "Keep it playful and suggestive at most — never explicit or vulgar, "
    "appropriate for Instagram. Under 400 characters total. "
    "Return ONLY the caption text, nothing else, no quotes."
)


def generate_caption(theme: dict, groq_api_key: str) -> str:
    tone     = random.choice(CAPTION_TONES)
    hashtags = random.choice(HASHTAG_SETS)
    is_story = random.random() < STORY_CHANCE

    user_prompt = (
        f"{theme['style']} shoot at {theme['setting']}, {theme['vibe']} energy. "
        f"Tone: {tone}."
    )

    try:
        r = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": _STORY_SYSTEM if is_story else _SYSTEM},
                    {"role": "user",   "content": user_prompt},
                ],
                "reasoning_effort": "low",
                "max_tokens": 300 if is_story else 200,
                "temperature": 0.9,
            },
            timeout=20,
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            if text:
                return f"{text}\n\n{hashtags}"
            print("  Groq returned empty content, using fallback")
        else:
            print(f"  Groq {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  Caption error: {e}")

    return _fallback(hashtags)


def _fallback(hashtags: str) -> str:
    captions = [
        "She didn't come here to blend in. Drop a 🔥 if you agree.",
        "Living in my own world — is there room for you? 👀",
        "Not your average girl next door. What's your vibe today?",
        "The version of me you weren't ready for. Ready now?",
        "She woke up like this. Lies? Maybe. Worth it? Always. 💋",
    ]
    return f"{random.choice(captions)}\n\n{hashtags}"
