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
    "#fashion #ootd #style #inspo #vibes #model #photography #beauty #luxury #editorial",
    "#lifestyle #aesthetic #goals #photooftheday #instadaily #beautifulgirl #fashionista #glam #iconic #stunning",
    "#travel #wanderlust #golden #look #explore #mood #outfitinspo #sunset #gorgeous #vibes",
    "#fitness #gym #glow #confidence #motivation #boss #queen #hustle #selflove #bodygoals",
    "#nightout #party #weekend #rooftop #nightlife #lit #looks #glam #luxurylife #drip",
]

_SYSTEM = (
    "You are a copywriter for a top Instagram influencer. "
    "Write captions that stop the scroll: short, punchy, unforgettable. "
    "Write as a confident real woman — never mention AI. "
    "End with a question or CTA. Under 150 characters. "
    "Return ONLY the caption text, nothing else, no quotes."
)


def generate_caption(theme: dict, groq_api_key: str) -> str:
    tone     = random.choice(CAPTION_TONES)
    hashtags = random.choice(HASHTAG_SETS)

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
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": user_prompt},
                ],
                "max_tokens": 120,
                "temperature": 0.9,
            },
            timeout=20,
        )
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip().strip('"')
            return f"{text}\n\n{hashtags}"
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
